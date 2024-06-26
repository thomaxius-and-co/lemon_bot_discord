import aiohttp
import enum
import os

import cache
import http_util
import logger
import perf
import retry

log = logger.get("OSU_API")

class Mode(enum.Enum):
    Standard = "0"
    Taiko = "1"
    Catch = "2"
    Mania = "3"

def head(xs):
    return next(iter(xs), None)

class User:
    def __init__(self, json):
        self.json = json
        self.id = json["user_id"]
        self.username = json["username"]

        if json["pp_rank"] is None:
            self.rank = None
        else:
            self.rank = int(json["pp_rank"])

        if json["pp_raw"] is None:
            self.pp = None
            self.pp_rounded = None
        else:
            self.pp = float(json["pp_raw"])
            self.pp_rounded = round(self.pp)

        if json["accuracy"] is None:
            self.accuracy = None
            self.accuracy_rounded = None
        else:
            self.accuracy = float(json["accuracy"])
            self.accuracy_rounded = round(self.accuracy, 2)

        self._best = None

class Play:
    def __init__(self, json):
        self.json = json
        self.beatmap_id = int(json["beatmap_id"])
        self.full_combo = json["perfect"] != "0"
        self.rank = self.parse_rank(json["rank"])
        self.mods_raw = int(json["enabled_mods"])
        self.score = int(json["score"])
        self.pp = float(json["pp"])
        self.pp_rounded = round(self.pp)
        self.date = json["date"]
        self.combo = int(json["maxcombo"])

        self._beatmap = None

    def parse_rank(self, rank):
        return "SS" if rank == "X" else rank

    @property
    def score_formatted(self):
        if self.score > 1000000:
            return "{0}M".format(round(self.score / 1000000.0, 1))
        if self.score > 1000:
            return "{0}k".format(round(self.score / 1000.0, 1))
        return "{0}".format(self.score)

    @property
    def mods(self):
        bitmasks = [
            ("NF", 1 << 0),
            ("EZ", 1 << 1),
            ("HD", 1 << 3),
            ("HR", 1 << 4),
            ("SD", 1 << 5),
            ("DT", 1 << 6),
            ("RX", 1 << 7),
            ("HT", 1 << 8),
            ("NC", 1 << 9),
            ("FL", 1 << 10),
            ("SO", 1 << 12),
            ("PF", 1 << 14),
        ]

        s = ""
        for name, mask in bitmasks:
            if self.mods_raw & mask:
                s += name
        return s

    @property
    def accuracy(self):
        count50 = int(self.json["count50"])
        count100 = int(self.json["count100"])
        count300 = int(self.json["count300"])
        countmiss = int(self.json["countmiss"])
        hits = 0
        hits += count50 * 50
        hits += count100 * 100
        hits += count300 * 300
        max_hits = (count50 + count100 + count300 + countmiss) * 300
        return float(hits) / float(max_hits) * 100

    @property
    def accuracy_rounded(self):
        return round(self.accuracy, 2)

    async def beatmap(self):
        if self._beatmap is None:
            self._beatmap = head(await beatmaps(self.beatmap_id))
        return self._beatmap

class Beatmap:
    def __init__(self, json):
        self.json = json
        self.beatmap_id = json["beatmap_id"]
        self.artist = json["artist"]
        self.title = json["title"]
        self.version = json["version"]
        self.stars = float(json["difficultyrating"])
        self.stars_rounded = round(self.stars, 2)

@retry.on_any_exception()
@perf.time_async("osu! API")
async def call_api(endpoint, params):
    params = params.copy()
    params.update({"k": os.environ["OSU_API_KEY"]})
    url = "https://osu.ppy.sh/api/%s%s" % (endpoint, http_util.make_query_string(params))
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        log.debug({
            "requestMethod": r.method,
            "requestUrl": str(r.url).replace(os.environ["OSU_API_KEY"], "<REDACTED>"),
            "responseStatus": r.status,
            "responseBody": await r.text(),
        })
        return await r.json()

async def user_by_id(user_id, game_mode):
    users = map(User, await call_api("get_user", {
        "type": "id",
        "u": user_id,
        "m": game_mode.value,
        "event_days": "1",
    }))
    return head(users)

async def user(name, game_mode):
    users = map(User, await call_api("get_user", {
        "type": "string",
        "u": name,
        "m": game_mode.value,
        "event_days": "1",
    }))
    return head(users)

async def user_best(name, limit, game_mode):
    if not (1 <= limit <= 100):
        raise ValueError("osu: invalid limit")

    return map(Play, await call_api("get_user_best", {
        "type": "string",
        "u": name,
        "m": game_mode.value,
        "limit": str(limit),
    }))

@cache.cache()
async def beatmaps(beatmap_id):
    raw = await call_api("get_beatmaps", {
        "m": "0",
        "b": str(beatmap_id),
        "limit": "1",
    })
    return list(map(Beatmap, raw))
