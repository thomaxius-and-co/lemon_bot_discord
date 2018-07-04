import aiohttp
import logger
import retry

# Credits to https://thesimpsonsquoteapi.glitch.me & Jason Luboff

log = logger.get("THE_SIMPSONS_API")

async def get_quote():
    async with aiohttp.ClientSession() as session:
        url = "https://thesimpsonsquoteapi.glitch.me/quotes"
        response = await session.get(url)
        log.debug("%s %s %s %s", response.method, response.url, response.status, await
        response.text())
        if response.status not in [200, 404]:
            raise Exception("Error fetching data from The Simpsons quotes api: HTTP status {0}".format(response.status))
        result = await response.json()
        if result:
            return result[0]['quote'], result[0]['character'], result[0]['image']
        else:
            raise Exception("Error fetching data from The Simpsons quotes api: HTTP status {0}".format(response.status))