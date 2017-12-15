import aiohttp
import json
from datetime import datetime

import logger
import perf
import retry
from time_util import to_helsinki, as_utc

log = logger.get("BITCOIN")

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

#todo: Redo this command properly, so it isn't as ugly
async def cmd_roadtobillion(client, message, user):
    btc_data = await get_current_price("Bitcoin")
    btc_eur = btc_data[0]["price_eur"]
    btc_usd = btc_data[0]["price_usd"]
    btc_percent_change_day = btc_data[0]["percent_change_24h"] #todo add plus symbol if positive number
    btc_updated = to_helsinki(as_utc(datetime.fromtimestamp(int(btc_data[0]["last_updated"]))))
    btc_amount_niske = round(int(0.00219075 * float(btc_eur)),3)
    btc_profit_niske = round(int(0.00219075 * float(btc_eur) - 35),3)
    operator_niske = '+' if btc_profit_niske > 0 else ''

    reply = ""

    reply += (
        "```\n"
        "Bitcoin price as of {time}\n"
        "{btc_eur} EUR\n"
        "{btc_usd} USD\n"
        "24h change: {btc_percent_change_day}\n"
        "Niske now has {amount_niske} EUR (profit: {operator_niske}{profit_niske} EUR)\n\n"
    ).format(
        time=btc_updated.strftime("%Y-%m-%d %H:%M"),
        btc_eur=round(float(btc_eur),3),
        btc_usd=round(float(btc_usd),3),
        btc_percent_change_day=btc_percent_change_day,
        amount_niske=btc_amount_niske,
        operator_niske=operator_niske,
        profit_niske=btc_profit_niske,
    )

    data = await get_current_price("Ethereum")
    eth_eur = data[0]["price_eur"]
    eth_usd = data[0]["price_usd"]
    eth_percent_change_day = data[0]["percent_change_24h"]
    eth_updated = to_helsinki(as_utc(datetime.fromtimestamp(int(data[0]["last_updated"]))))

    eth_amount_thomaxius = round(int(0.25 * float(eth_eur)),3)
    eth_profit_thomaxius = round(int(0.25 * float(eth_eur) - 100),3)
    operator_thomaxius = '+' if eth_profit_thomaxius > 0 else ''

    eth_amount_chimppa = round(int(0.4268 * float(eth_eur)),3)
    eth_profit_chimppa = round(int(0.4268 * float(eth_eur) - 250),3)
    operator_chimppa = '+' if eth_profit_chimppa > 0 else ''

    eth_amount_niske = round(int(0.04309901 * float(eth_eur)),3)
    eth_profit_niske = round(int(0.04309901 * float(eth_eur) - 25), 3)
    operator_niske = '+' if eth_profit_niske > 0 else ''




    reply += (
        "Ethereum price as of {time}\n"
        "{eth_eur} EUR\n"
        "{eth_usd} USD\n"
        "24h change: {eth_percent_change_day}\n"
        "Thomaxius now has {amount_thomaxius} EUR (profit: {operator_thomaxius}{profit_thomaxius} EUR)\n"
        "Chimppa now has {amount_chimppa} EUR (profit: {operator_chimppa}{profit_chimppa} EUR)\n"
        "Niske now has {amount_niske} EUR (profit: {operator_niske}{profit_niske} EUR)\n\n"
    ).format(
        time=eth_updated.strftime("%Y-%m-%d %H:%M"),
        eth_eur=round(float(eth_eur),3),
        eth_usd=round(float(eth_usd),3),
        eth_percent_change_day=eth_percent_change_day,
        amount_thomaxius=eth_amount_thomaxius,
        operator_thomaxius=operator_thomaxius,
        profit_thomaxius=eth_profit_thomaxius,
        amount_chimppa=eth_amount_chimppa,
        operator_chimppa=operator_chimppa,
        profit_chimppa=eth_profit_chimppa,
        amount_niske=eth_amount_niske,
        operator_niske=operator_niske,
        profit_niske=eth_profit_niske,
    )
    litecoin_data = await get_current_price("Litecoin")
    ltc_eur = litecoin_data[0]["price_eur"]
    ltc_usd = litecoin_data[0]["price_usd"]
    ltc_percent_change_day = litecoin_data[0]["percent_change_24h"]
    ltc_updated = to_helsinki(as_utc(datetime.fromtimestamp(int(litecoin_data[0]["last_updated"]))))

    ltc_amount_thomaxius = round(int(0.3247 * float(ltc_eur)),3)
    ltc_profit_thomaxius = round(int(0.3247 * float(ltc_eur) - 100),3)
    operator_thomaxius = '+' if ltc_profit_thomaxius > 0 else ''

    ltc_amount_chimppa = round(int(1.0921 * float(ltc_eur)),3)
    ltc_profit_chimppa = round(int(1.0921 * float(ltc_eur) - 250),3)
    operator_chimppa = '+' if ltc_profit_chimppa > 0 else ''

    ltc_amount_niske = round(int(0.10539865 * float(ltc_eur)),3)
    ltc_profit_niske = round(int(0.10539865 * float(ltc_eur) - 25),3)
    operator_niske = '+' if ltc_profit_niske > 0 else ''


    reply += (

        "Litecoin price as of {time}\n"
        "{ltc_eur} EUR\n"
        "{ltc_usd} USD\n"
        "24h change: {ltc_percent_change_day}\n"
        "Thomaxius now has {amount_thomaxius} EUR (profit: {operator_thomaxius}{profit_thomaxius} EUR)\n"
        "Chimppa now has {amount_chimppa} EUR (profit: {operator_chimppa}{profit_chimppa} EUR)\n"
        "Niske now has {amount_niske} EUR (profit: {operator_niske}{profit_niske} EUR)\n\n"        
        "Chimppa's total profit: {chimppa_total_profit}\n"
        "Thomaxius' total profit: {thomaxius_total_profit}\n"
        "Niske's total profit: {niske_total_profit}\n"
        "```"
    ).format(
        time=ltc_updated.strftime("%Y-%m-%d %H:%M"),
        ltc_eur=round(float(ltc_eur),3),
        ltc_usd=round(float(ltc_usd),3),
        ltc_percent_change_day=ltc_percent_change_day,
        amount_thomaxius=ltc_amount_thomaxius,
        operator_thomaxius=operator_thomaxius,
        profit_thomaxius=ltc_profit_thomaxius,
        amount_chimppa=ltc_amount_chimppa,
        operator_chimppa=operator_chimppa,
        profit_chimppa=ltc_profit_chimppa,
        amount_niske=ltc_amount_niske,
        operator_niske=operator_niske,
        profit_niske=ltc_profit_niske,
        chimppa_total_profit='+' + str(eth_profit_chimppa + ltc_profit_chimppa) + ' EUR' if ((eth_profit_chimppa + ltc_profit_chimppa) > 0)
        else '' + str(eth_profit_chimppa + ltc_profit_chimppa) + ' EUR',
        thomaxius_total_profit='+' + str(eth_profit_thomaxius + ltc_profit_thomaxius) + ' EUR' if ((eth_profit_thomaxius + ltc_profit_thomaxius) > 0)
        else '' + str(eth_profit_thomaxius + ltc_profit_thomaxius) + ' EUR',
        niske_total_profit = '+' + str(eth_profit_niske + ltc_profit_niske + btc_profit_niske) + ' EUR' if ((eth_profit_niske + ltc_profit_niske + btc_profit_niske) > 0) else '' + str(eth_profit_niske + ltc_profit_niske) + ' EUR'
    )
    await client.send_message(message.channel, reply)


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
        eur=round(float(eur),3),
        usd=round(float(usd),3),
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