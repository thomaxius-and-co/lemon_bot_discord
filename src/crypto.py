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
        "bitcoin": cmd_bitcoin,
        "btc": cmd_bitcoin,
        "roadtobillion": cmd_roadtobillion,
        "rtb": cmd_roadtobillion,
        "crypto": cmd_crypto
    }

coins = ['ethereum', 'bitcoin', 'litecoin', 'bitcoin-cash']

coins_dict = {'eth': 'Ethereum',
              'btc': 'Bitcoin',
              'ltc': 'Litecoin',
              'bch': 'Bitcoin-Cash'}

coin_owners_dict = {
    'Ethereum': [('Chimppa',0.4268,250), ('Niske',0.0759247,50), ('Thomaxius',0.24297085,100)], #Coin name, coin amount, € amount bought with
    'Litecoin': [('Chimppa',1.0921, 250), ('Niske',0.18639323,50), ('Thomaxius',0.3247,100)],
    'Bitcoin': [('Niske',0.00372057,60)],
    'Ripple': [('Thomaxius',78,64.4)],
    'Stellar': [('Thomaxius',50,10.1)],
    'Iota': [('Thomaxius',10,45.25)],
    'Verge': [('Thomaxius',163.736,20)]
}

profit_dict = {#name: (amountofcoinineur, amountboughtwith)
}

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

        msg += ('\n%s total profit: %s%s EUR (%s%%)' % (owner, '+' if (total_profit > 0) else '', round(total_profit,4), '+' + str(round(profit_percentage,2)) if profit_percentage > 0 else ''))
    profit_dict.clear()
    return msg + '```'

async def rtb_get_crypto_price(coin):
    coin_data = await get_current_price(coin)
    coin_price_eur = coin_data[0]["price_eur"]
    coin_price_usd = coin_data[0]["price_usd"]
    coin_name = coin_data[0]["name"]
    percent_change_day = '+' + str(coin_data[0]["percent_change_24h"]) if (float(coin_data[0]["percent_change_24h"]) > 0) else coin_data[0]["percent_change_24h"]
    updated = to_helsinki(as_utc(datetime.fromtimestamp(int(coin_data[0]["last_updated"]))))

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

    percent_change_day = '+' + str(data[0]["percent_change_24h"]) if (float(data[0]["percent_change_24h"]) > 0) else data[0]["percent_change_24h"]

    return ((
        "\n"
        "{name}:\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "24h change: {percent_change_day}%\n"
    ).format(
        name=name,
        eur=round(float(eur),2),
        usd=round(float(usd),2),
        percent_change_day=percent_change_day
    ))

async def cmd_bitcoin(client, message, user):
    await client.send_message(message.channel, "This command is obsolete and replaced by !crypto.")

async def cmd_crypto(client, message, arg):
    if arg and (arg.lower() not in coins):
        arg = coins_dict.get(arg.lower(), None)
        if not arg:
            await client.send_message(message.channel, 'Available cryptocoins: %s' % coins)
            return
    await client.send_message(message.channel, await message_builder(arg if arg else None))

async def message_builder(arg):
    if arg:
        msg = ('%s price as of %s:```' % (arg.title(), await get_date_fetched()))
        msg += await get_crypto_price(arg)
        return msg + '```'
    msg = 'Crypto prices as of %s:```' % await get_date_fetched()
    for coin in coins:
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

async def get_date_fetched():
    url = "https://api.coinmarketcap.com/v1/ticker/Bitcoin/?convert=EUR"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))
        text = await r.text()
        return to_helsinki(as_utc(datetime.fromtimestamp(int(json.loads(text, encoding="utf-8")[0]['last_updated'])))).strftime("%Y-%m-%d %H:%M")
