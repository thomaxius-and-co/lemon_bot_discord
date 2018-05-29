import aiohttp
import logger
import os

import retry
import http_util

log = logger.get("FACEIT_API")

FACEIT_API_KEY = os.environ.get("FACEIT_API_KEY", None)
AUTH_HEADER = {"Authorization": "Bearer {0}".format(FACEIT_API_KEY)}

class UserNotFound(Exception):
    pass

class UnknownError(Exception):
    def __init__(self, response):
        super().__init__("Unknown faceit error: HTTP Status {0}".format(response.status))
        self.response = response

async def player_history(player_id, offset=0, limit=20):
    query = {
        "offset": str(offset),
        "limit": str(limit),
    }

    response = await _call_api("/players/{0}/history".format(player_id), query=query)
    json = await response.json()
    if response.status == 200:
        return json
    elif response.status == 404:
        raise UserNotFound("User not found (player_id: {0})".format(player_id))
    else:
        raise UnknownError(response)

async def user(nickname):
    response = await _call_api("/players", query={"nickname": nickname})
    json = await response.json()
    if response.status == 200:
        return json
    elif response.status == 404:
        raise UserNotFound("User not found (nickname: {0})".format(nickname))
    else:
        raise UnknownError(response)

async def ranking(player_id, region="EU", game_id="csgo"):
    response = await _call_api("/rankings/games/{0}/regions/{1}/players/{2}".format(game_id, region, player_id))
    json = await response.json()
    if response.status == 200:
        return json.get("position", None)
    elif response.status == 404:
        raise UserNotFound("User not found (player_id: {0})".format(player_id))
    else:
        raise UnknownError(response)

@retry.on_any_exception(max_attempts = 10, init_delay = 1, max_delay = 30)
async def _call_api(path, query=None):
    url = "https://open.faceit.com/data/v4{0}{1}".format(path, http_util.make_query_string(query))
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=AUTH_HEADER)
        log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())
        if response.status not in [200, 404]:
            raise Exception("Error fetching data from faceit: HTTP status {0}".format(response.status))
        return response
