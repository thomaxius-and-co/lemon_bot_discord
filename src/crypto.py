import aiohttp
import json
from datetime import datetime

import logger
import perf
import retry
from time_util import to_helsinki, as_utc

log = logger.get("CRYPTO")

def register(client):
    return {
        "roadtobillion": cmd_roadtobillion,
        "rtb": cmd_roadtobillion,
        "crypto": cmd_crypto
    }

available_coins_list = []

coin_symbols = {  #{'btc': 'bitcoin'
     }

available_coins = {  #'bitcoin': 'bitcoin'
     }

default_coins = ['Bitcoin', 'Ethereum', 'Bitcoin-Cash', 'Litecoin', 'Ripple']

coin_owners_dict = {
    'Ethereum': [('Chimppa',0.4268,250), ('Niske',0.0759247,50), ('Thomaxius',0.4419598,292)], #Coin name, coin amount, € amount bought with
    'Litecoin': [('Chimppa',1.0921, 250), ('Niske',0.18639323,50), ('Thomaxius',0.1747,50.84)],
    'Bitcoin': [('Niske',0.00372057,60)],
    'Ripple': [('Thomaxius',83,120.3)],
    'Stellar': [('Thomaxius',50,10.1)],
    'Iota': [('Thomaxius',10,45.25)],
    'Verge': [('Thomaxius',163.736,20)],
    'Bytecoin-bcn': [('Thomaxius',2000,13)],
    'Dent': [('Thomaxius',887,40)],
    'Siacoin': [('Thomaxius',100,14)],
    #'Latoken': [('Thomaxius',30,25)],
    'nxt': [('Thomaxius',20,10)]
}

profit_dict = {  #name: (amountofcoinineur, amountboughtwith)
}

async def main():
    await get_available_coins()
    log.info('tasks started')

async def get_available_coins():
    json = await get_all_coins()
    for coin in json:
        coin_name = coin.get('name')
        coin_id = coin.get('id')
        coin_symbol = coin.get('symbol')
        available_coins.update({coin_name.lower():coin_id.lower()})
        coin_symbols.update({coin_symbol.lower():coin_id.lower()})
        available_coins_list.append(coin_name)

async def cmd_roadtobillion(client, message, _):
    await client.send_message(message.channel, await rtb_message_builder())

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

async def rtb_get_crypto_price(coin):
    coin_data = await get_current_price(coin)
    coin_price_eur = coin_data[0]["price_eur"]
    coin_price_usd = coin_data[0]["price_usd"]
    coin_name = coin_data[0]["name"]
    percent_change_day = '+' + str(coin_data[0]["percent_change_24h"]) if (float(coin_data[0]["percent_change_24h"]) > 0) else coin_data[0]["percent_change_24h"]

    return ((
        "\n"
        "{name} price:\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "24h change: {percent_change_day}%\n"
    ).format(
        name=coin_name,
        eur=round(float(coin_price_eur),2),
        usd=round(float(coin_price_usd),2),
        percent_change_day=percent_change_day
    )) + await get_coin_owners_message(coin, coin_price_eur)

async def get_coin_owners_message(coin, coin_price_eur):
    reply = ''
    for owner in coin_owners_dict.get(coin):
        name = owner[0]
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

async def get_crypto_price(coin):
    data = await get_current_price(coin)
    eur = data[0]["price_eur"]
    usd = data[0]["price_usd"]
    name = data[0]["name"]
    market_cap_usd = data[0]["market_cap_usd"]
    coin_rank = data[0]["rank"]
    percent_change_hour = '+' + str(data[0]["percent_change_1h"]) if (float(data[0]["percent_change_1h"]) > 0) else data[0]["percent_change_1h"]
    percent_change_day = '+' + str(data[0]["percent_change_24h"]) if (float(data[0]["percent_change_24h"]) > 0) else data[0]["percent_change_24h"]

    return ((
        "\n"
        "{name}:\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "Market cap: {market_cap_usd} USD\n"
        "Rank: {rank}\n"
        "1h change: {percent_change_hour}%\n"
        "24h change: {percent_change_day}%\n"
    ).format(
        name=name,
        eur=round(float(eur),2),
        usd=round(float(usd),2),
        market_cap_usd=market_cap_usd,
        rank=coin_rank,
        percent_change_hour=percent_change_hour,
        percent_change_day=percent_change_day
    ))

async def cmd_crypto(client, message, arg):
    arg = arg.lower()
    if arg and (arg == 'list'):
        await client.send_message(message.channel, 'Available cryptocoins: %s' % ', '.join(available_coins_list))
        return
    if arg and (arg not in available_coins):
        arg = coin_symbols.get(arg, None)
        if not arg:
            if not available_coins_list:
                await get_available_coins()
            await client.send_message(message.channel, 'Unknown coin. You can check available '
                                                       'coins with !crypto list' % ', '.join(available_coins_list))
            return
    else:
        arg = available_coins.get(arg)
    await client.send_message(message.channel, await message_builder(arg if arg else None))

async def message_builder(arg):
    if arg:
        msg = ('%s price as of %s:```' % (arg.title(), await get_date_fetched()))
        msg += await get_crypto_price(arg)
        return msg + '```'
    msg = 'Crypto prices as of %s:```' % await get_date_fetched()
    for coin in default_coins:
        msg += await get_crypto_price(coin)
    return msg + '```'

@retry.on_any_exception
@perf.time_async("Coinmarketcap API")
async def get_current_price(coin):
    url = "https://api.coinmarketcap.com/v1/ticker/%s/?convert=EUR" % coin
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))

        text = await r.text()
        return json.loads(text, encoding="utf-8")

async def get_all_coins():
    url = "https://api.coinmarketcap.com/v1/ticker/"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))
        text = await r.text()
        return json.loads(text, encoding="utf-8")

async def get_date_fetched():
    url = "https://api.coinmarketcap.com/v1/ticker/Bitcoin/?convert=EUR"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))
        text = await r.text()
        return to_helsinki(as_utc(datetime.fromtimestamp(int(json.loads(text, encoding="utf-8")[0]['last_updated'])))).strftime("%Y-%m-%d %H:%M")
