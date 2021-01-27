from datetime import datetime
from pprint import pprint, pformat
import aiohttp
import json
import os

from time_util import to_helsinki, as_utc
import http_util
import logger
import perf
import retry

log = logger.get("CRYPTO")

def register(client):
    if "COINMARKETCAP_API_KEY" not in os.environ:
        log.warning("COINMARKETCAP_API_KEY not defined")
        return

    return {
        "roadtobillion": cmd_roadtobillion,
        "rtb": cmd_roadtobillion,
    }


profit_dict = {}
coin_owners_dict = {
    'ETH': [('Chimppa',0.4268,250), ('Niske',0.0759247,50), ('Thomaxius',0.4419598,292)], #Coin name, coin amount, € amount bought with
    'LTC': [('Chimppa',1.0921, 250), ('Niske',0.18639323,50), ('Thomaxius',0.1747,50.84)],
    'BTC': [('Niske',0.00372057,60)],
    'XLA': [('Thomaxius',179,220.3)],
    'XLM': [('Thomaxius',50,10.1)],
    'MIOTA': [('Thomaxius',10,45.25)],
    'XVG': [('Thomaxius',163.736,20)],
    'BCN': [('Thomaxius',2000,13)],
    'DENT': [('Thomaxius',887,40)],
    'SC': [('Thomaxius',100,14)],
    'LA': [('Thomaxius',30,25)],
    'QVT': [('Thomaxius',44,35)],
    'NXT': [('Thomaxius',20,10)]
}

async def main():
    if "COINMARKETCAP_API_KEY" not in os.environ:
        log.warning("COINMARKETCAP_API_KEY not defined")
        return

    await get_available_coins()
    log.info('tasks started')

async def get_available_coins():
    json = await get_all_coins()
    with open("coins.txt", "w") as f:
        f.write(pformat(json))

    coins = json.get("data")
    pprint(coins)
    for coin in coins:
        coin_name = coin.get('name')
        coin_id = coin.get('id')
        coin_symbol = coin.get('symbol')

async def cmd_roadtobillion(client, message, _):
    await message.channel.send(await rtb_message_builder())

async def rtb_message_builder():
    msg = '```'
    for coin in coin_owners_dict:
        msg += await rtb_get_crypto_price(coin)
    for owner in profit_dict:
        value, buy_value = profit_dict.get(owner)
        total_profit = value - buy_value
        profit_percentage = total_profit / buy_value * 100

        pct_str = ('+' if profit_percentage >= 0 else '') + str(round(profit_percentage, 2))
        msg += ('\n%s total profit: %s%s EUR (%s%%)' % (owner, '+' if (total_profit > 0) else '', round(total_profit,4), pct_str))
    profit_dict.clear()
    return msg + '```'

async def rtb_get_crypto_price(symbol):
    response = await get_current_price(symbol)
    if symbol not in response["data"]:
        log.info("Crypto not found")
        coin_price_eur = 0
        return "\n{name} price:\n{eur} EUR\n".format(name=coin_name, eur=0) + await get_coin_owners_message(symbol, coin_price_eur)

    coin_data = response["data"][symbol]
    pprint(coin_data)

    eur_quote = coin_data.get("quote", {}).get("EUR", {})
    pprint(eur_quote)
    coin_price_eur = await get_correct_type(eur_quote.get("price", None), 2)
    coin_name = coin_data.get("name", symbol)
    percent_change_day_str = await get_percent_change_day_str(eur_quote.get("percent_change_24h", None))
    if not coin_price_eur:
        return "\nNot showing data for %s as it is unavailable at this time.\n" % coin_name
    return ((
        "\n"
        "{name} price:\n"
        "{eur} EUR\n"
        "24h change: {percent_change_day}\n"
    ).format(
        name=coin_name,
        eur=coin_price_eur,
        percent_change_day=percent_change_day_str
    )) + await get_coin_owners_message(symbol, coin_price_eur) if coin_price_eur else ''

async def get_correct_type(arg, decimals):
    return round(float(arg), decimals) if arg is not None else 0

async def get_percent_change_day_str(percent_change_day):
    if ((percent_change_day is not None) and (float(percent_change_day) > 0)):
        return f"+{percent_change_day}%"
    elif ((percent_change_day is not None) and (float(percent_change_day) < 0)):
        return f"{percent_change_day}%"
    elif percent_change_day is None:
        return "-"

@perf.time_async("get_coin_owners_message")
async def get_coin_owners_message(symbol, coin_price_eur):
    reply = ''
    for owner in coin_owners_dict.get(symbol):
        name = owner[0]
        pprint(symbol)
        pprint(coin_price_eur)
        pprint(owner)
        amount_eur = round(owner[1]*float(coin_price_eur),2)
        total_cost = owner[2]
        profit_eur = amount_eur
        total_profit = round(profit_eur-total_cost,3)
        operator = '+' if profit_eur-total_cost > 0 else ''
        if profit_dict.get(name, None) is None:
            profit_dict.update({name:(profit_eur, total_cost)})
        else:
            profit_owner = profit_dict.get(name)
            current_profit = profit_owner[0]
            current_cost = profit_owner[1]
            profit_dict.update({name:(current_profit+profit_eur,current_cost+total_cost)})
        reply += ('%s now has %s EUR (profit %s%s EUR)\n' % (name, amount_eur, operator, total_profit))
    return reply

async def get_current_price(symbol):
    return await call_api("/v1/cryptocurrency/quotes/latest", { "convert": "EUR", "symbol": symbol })

async def get_all_coins():
    return await call_api("/v1/cryptocurrency/listings/latest", {})

@retry.on_any_exception()
@perf.time_async("CoinMarketCap API")
async def call_api(endpoint, params):
    headers = {"X-CMC_PRO_API_KEY": os.environ["COINMARKETCAP_API_KEY"]}
    url = f"https://pro-api.coinmarketcap.com{endpoint}{http_util.make_query_string(params)}"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers=headers)
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))
        return await r.json()
