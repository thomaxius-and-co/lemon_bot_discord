import os
import json
import requests

def make_query_string(params):
    return "?" + "&".join(map(lambda x: "=".join(x), params.items()))

def call_api(endpoint, params):
    url = "https://osu.ppy.sh/api/%s%s" % (endpoint, make_query_string(params))
    res = requests.get(url)
    return json.loads(res.text)

def user(name):
    return call_api("get_user", {
        "k": os.environ["OSU_API_KEY"],
        "type": "u",
        "u": name,
        "event_days": "1",
    })
