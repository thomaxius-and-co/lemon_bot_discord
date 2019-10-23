import aiohttp
import asyncio
import os

import http_util
import logger
import retry

log = logger.get("FACEIT_API")

FACEIT_API_KEY = os.environ.get("FACEIT_API_KEY", None)
AUTH_HEADER = {"Authorization": "Bearer {0}".format(FACEIT_API_KEY)}


class NotFound(Exception):
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
        raise NotFound("User not found (player_id: {0})".format(player_id))


async def user(nickname):
    response = await _call_api("/players", query={"nickname": nickname})
    json = await response.json()
    if response.status == 200:
        return json
    elif response.status == 404:
        raise NotFound("User not found (nickname: {0})".format(nickname))


async def user_by_id(player_id):
    response = await _call_api("/players/{0}".format(player_id))
    json = await response.json()
    if response.status == 200:
        return json
    elif response.status == 404:
        raise NotFound("User not found (player_id: {0})".format(player_id))


async def ranking(player_id, region="EU", game_id="csgo"):
    response = await _call_api("/rankings/games/{0}/regions/{1}/players/{2}".format(game_id, region, player_id))
    json = await response.json()
    if response.status == 200:
        return json.get("position", None)
    elif response.status == 404:
        raise NotFound("User not found (player_id: {0})".format(player_id))


async def match_stats(match_id):
    response = await _call_api("""/matches/{0}/stats""".format(match_id))
    json = await response.json()
    if response.status == 200:
        return json.get("rounds", None)
    elif response.status == 404:
        raise NotFound("Match not found (match id: {0})".format(match_id))


async def player_match_history(player_id, from_timestamp=0, to_timestamp=None, limit=100):
    log.info("timestamp: %s" % from_timestamp)
    from_timestamp = int(from_timestamp)
    log.info("timestamp2: %s" % from_timestamp)
    if to_timestamp:
        to_timestamp_param = "&to={0}".format(to_timestamp)
    else:
        to_timestamp_param = ""
    response = await _call_api("""/players/{0}/history?game=csgo&from={1}{2}&offset=0&limit={3}""".format(player_id, from_timestamp, to_timestamp_param, limit))
    json = await response.json()
    if response.status == 200:
        return json.get("items", None)
    elif response.status == 404:
        return None


async def match(matchid):
    response = await _call_api("""/matches/{0}""".format(matchid))
    json = await response.json()
    if response.status == 200:
        return json
    elif response.status == 404:
        return None


@retry.on_any_exception(max_attempts = 10, init_delay = 1, max_delay = 30)
async def _call_api(path, query=None):
    url = "https://open.faceit.com/data/v4{0}{1}".format(path, http_util.make_query_string(query))
    async with aiohttp.ClientSession() as session:
        for ratelimit_delay in retry.jitter(retry.exponential(1, 128)):
            response = await session.get(url, headers=AUTH_HEADER)
            log.debug("%s %s %s %s", response.method, response.url, response.status, await response.text())

            # Hit ratelimits! Always retry after a delay
            if response.status == 429:
                log.info(f"Ratelimited, retrying in {round(ratelimit_delay, 1)} seconds")
                await asyncio.sleep(ratelimit_delay)
                continue

            if response.status not in [200, 404]:
                raise UnknownError(response)
            return response
