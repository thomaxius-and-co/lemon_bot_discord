import aiohttp
import logger

log = logger.get("FACEIT_API")

async def ranking(guid, area="EU"):
    url = "https://api.faceit.com/ranking/v1/globalranking/csgo/" + area + "/" + guid
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())
        result = await response.json()
        return result.get("payload", 0)

async def user(nickname):
    url = "https://api.faceit.com/api/nicknames/" + nickname
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())

        if response.status != 200:
            log.error("Error fetching data from faceit: HTTP status %d", response.status)
            return None, "Could not fetch data from faceit"

        result = await response.json()
        if result.get('result', None) == 'error':
            log.error(result["message"].title())
            return None, result["message"].title()
        if not result or (result.get('result', None) is None):
            log.error('Unknown error: %s', result)
            return None, 'There was an error, pls report'
        return result.get("payload", {}), None
