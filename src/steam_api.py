import os
import aiohttp
import json
import cache

import logger
import perf

log = logger.get("STEAM_API")

class Game:
    def __init__(self, json):
        self.name = json.get("gameName", "N/A")

class OwnedGame:
    def __init__(self, json):
        self.appid = json.get("appid")
        self.playtime_forever = json.get("playtime_forever", 0)
        self.playtime_2weeks = json.get("playtime_2weeks", 0)

def make_query_string(params):
    return "?" + "&".join(map(lambda x: "=".join(map(str, x)), params.items()))

@perf.time_async("Steam API")
async def call_api(endpoint, params):
    params = params.copy()
    params.update({"key": os.environ["STEAM_API_KEY"], "format": "json"})
    url = "https://api.steampowered.com/%s%s" % (endpoint, make_query_string(params))
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        log.info("%s %s %s %s", r.method, str(r.url).replace(os.environ["STEAM_API_KEY"], "<REDACTED>"), r.status, await r.text())
        return await r.json()

@cache.cache(ttl = cache.HOUR)
async def owned_games(steamid):
    raw = await call_api("IPlayerService/GetOwnedGames/v0001/", {"steamid": steamid})
    return list(map(OwnedGame, raw["response"]["games"]))

@cache.cache(ttl = cache.WEEK)
async def game(appid):
    raw = await call_api("ISteamUserStats/GetSchemaForGame/v2/", {"appid": appid})
    return Game(raw["game"])

@cache.cache(ttl = cache.WEEK)
async def steamid(username):
    raw = await call_api("ISteamUser/ResolveVanityURL/v0001/", {"vanityurl": username.lower()})
    return raw["response"].get("steamid", None)

@perf.time_async("Steam API")
async def call_appdetails(appid):
    url = "http://store.steampowered.com/api/appdetails?appids={appid}".format(appid=appid)
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        log.info("%s %s %s %s", r.method, r.url, r.status, await r.text())
        return await r.json()

@cache.cache()
async def appdetails(appid):
    raw = await call_appdetails(appid)
    return raw[str(appid)].get("data", {"name": "pls report error to thomaxius"})
