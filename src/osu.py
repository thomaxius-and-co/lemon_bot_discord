import os
import json
import aiohttp

def make_query_string(params):
    return "?" + "&".join(map(lambda x: "=".join(x), params.items()))

async def call_api(endpoint, params):
    url = "https://osu.ppy.sh/api/%s%s" % (endpoint, make_query_string(params))
    async with aiohttp.get(url) as r:
        return await r.json()

async def user(name):
    return await call_api("get_user", {
        "k": os.environ["OSU_API_KEY"],
        "type": "u",
        "u": name,
        "event_days": "1",
    })
