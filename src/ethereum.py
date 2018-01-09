import aiohttp
import json
from datetime import datetime

import logger
import perf
import retry
from time_util import as_utc, to_helsinki

log = logger.get("ethereum")

def register(client):
    return {
        "ethereum": cmd_ethereum,
        "eth": cmd_ethereum,
    }


async def cmd_ethereum(client, message, user):
    data = await get_current_price()

    eur = data[0]["price_eur"]
    usd = data[0]["price_usd"]
    updated = to_helsinki(as_utc(datetime.fromtimestamp(int(data[0]["last_updated"]))))

    reply = (
        "Ethereum price as of {time}\n"
        "```\n"
        "{eur} EUR\n"
        "{usd} USD\n"
        "Thomaxius now has {amount} EUR (profit: {profit} EUR)"
        "```"
    ).format(
        time=updated.strftime("%Y-%m-%d %H:%M"),
        eur=round(float(eur),3),
        usd=round(float(usd),3),
        amount=round(int(0.25 * float(eur)),3),
        profit=round(int(0.25 * float(eur)-100),3)
    )
    await client.send_message(message.channel, reply)

@retry.on_any_exception()
@perf.time_async("Coinmarketcap API")
async def get_current_price():
    url = "https://api.coinmarketcap.com/v1/ticker/Ethereum/?convert=EUR"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers={"Accept": "application/json"})
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        if r.status != 200:
            raise Exception("HTTP status error {0}".format(r.status))

        text = await r.text()
        return json.loads(text, encoding="utf-8")
