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
        "ethereum": cmd_ethereum,
        "eth": cmd_ethereum,
        "crypto": cmd_crypto
    }

coins = ['Ethereum', 'Bitcoin', 'Litecoin', 'Bitcoin-Cash']

async def cmd_ethereum(client, message, user):
    data = await get_current_price("Ethereum")
    eur = data[0]["price_eur"]
    usd = data[0]["price_usd"]
    percent_change_day = data[0]["percent_change_24h"]
    updated = to_helsinki(as_utc(datetime.fromtimestamp(int(data[0]["last_updated"]))))

    reply = (
        "Ethereum price as of {time}\n"
        "```\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "24h change: {percent_change_day}\n"
        "Thomaxius now has {amount} EUR (profit: {profit} EUR)"
        "```"
    ).format(
        time=updated.strftime("%Y-%m-%d %H:%M"),
        eur=round(float(eur),3),
        usd=round(float(usd),3),
        percent_change_day=percent_change_day,
        amount=round(int(0.25 * float(eur)),3),
        profit=round(int(0.25 * float(eur)-100),3)
    )
    await client.send_message(message.channel, reply +  "This command is obsolete and replaced by !crpyto.'")

async def get_crypto_price(coin):
    data = await get_current_price(coin)
    eur = data[0]["price_eur"]
    usd = data[0]["price_usd"]
    name = data[0]["name"]
    percent_change_day = data[0]["percent_change_24h"]

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
    await client.send_message(message.channel, "This command is obsolete and replaced by !crpyto.")

async def cmd_crypto(client, message, _):
    await client.send_message(message.channel, await message_builder())

async def message_builder():
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