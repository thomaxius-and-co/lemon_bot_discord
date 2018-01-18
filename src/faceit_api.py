import aiohttp
import logger
import retry

log = logger.get("FACEIT_API")

@retry.on_any_exception(max_attempts = 3, init_delay = 0.1, max_delay = 1)
async def ranking(guid, area="EU"):
    url = "https://api.faceit.com/ranking/v1/globalranking/csgo/" + area + "/" + guid
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())
        result = await response.json()
        return result.get("payload", 0)

@retry.on_any_exception(max_attempts = 3, init_delay = 0.1, max_delay = 1)
async def user(nickname):
    url = "https://api.faceit.com/api/nicknames/" + nickname
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())

        if response.status not in [200, 404]:
            raise Exception("Error fetching data from faceit: HTTP status {0}".format(response.status))

        result = await response.json()
        if result.get('result', None) == 'error':
            log.error(result["message"].title())
            return None, result["message"].title()
        if not result or (result.get('result', None) is None):
            log.error('Unknown error: %s', result)
            return None, 'There was an error, pls report'
        return result.get("payload", {}), None
