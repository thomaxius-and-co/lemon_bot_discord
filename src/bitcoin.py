import aiohttp
import json
from datetime import datetime

import logger
import perf
import retry
from time_util import to_helsinki

log = logger.get("BITCOIN")

def register(client):
    return {
        "bitcoin": cmd_bitcoin,
        "btc": cmd_bitcoin,
    }

def parse_iso_time(time_str):
    # Remove the ':' in '+00:00' because strptime doesn't understand it...
    time_str = time_str[:-3] + time_str[-2:]
    time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")
    return to_helsinki(time_obj)

async def cmd_bitcoin(client, message, user):
    data = await get_current_price()
    eur = data["bpi"]["EUR"]["rate_float"]
    usd = data["bpi"]["USD"]["rate_float"]
    updated = parse_iso_time(data["time"]["updatedISO"])

    reply = (
        "Bitcoin price as of {time}\n"
        "```\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "```"
    ).format(
        time=updated.strftime("%Y-%m-%d %H:%M"),
        eur=format_money(eur),
        usd=format_money(usd)
    )
    await client.send_message(message.channel, reply)

def format_money(amount):
    return "{0:10,.2f}".format(amount).replace(",", " ").replace(".", ",")

@retry.on_any_exception
@perf.time_async("CoinDesk API")
async def get_current_price():
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))

        text = await r.text()
        return json.loads(text, encoding="utf-8")
