import aiohttp
import logger

# Credits to https://thesimpsonsquoteapi.glitch.me & Jason Luboff

log = logger.get("THE_SIMPSONS_API")

async def get_quote():
    async with aiohttp.ClientSession() as session:
        url = "https://thesimpsonsquoteapi.glitch.me/quotes"
        response = await session.get(url)
        log.debug({
            "requestMethod": response.method,
            "requestUrl": str(response.url),
            "responseStatus": response.status,
            "responseBody": await response.text(),
        })
        if response.status not in [200, 404]:
            raise RuntimeError("Error fetching data from The Simpsons quotes api: HTTP status {0}".format(response.status))
        result = await response.json()
        if result:
            return result[0]['quote'], result[0]['character'], result[0]['image']
        else:
            raise RuntimeError("Error fetching data from The Simpsons quotes api: HTTP status {0}".format(response.status))