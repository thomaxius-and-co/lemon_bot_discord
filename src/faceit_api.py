import aiohttp
import logger

log = logger.get("FACEIT_API")

async def ranking(guid, area="EU"):
    url = "https://api.faceit.com/ranking/v1/globalranking/csgo/" + area + "/" + faceit_guid
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("GET %s %s %s", response.url, response.status, await response.text())
        result = await response.json()
        return result.get("payload", 0)

async def user(nickname):
    url = "https://api.faceit.com/api/nicknames/" + nickname
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("GET %s %s %s", response.url, response.status, await response.text())
        result = await response.json()
        if result['result'] == 'error':
            return None
        return result.get("payload", None)
