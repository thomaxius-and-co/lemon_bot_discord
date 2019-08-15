import datetime
import aiohttp

from time_util import as_utc, to_helsinki
import cache
import logger

log = logger.get("GROOM")

SERVICE_BASIC = 27
SERVICE_SPECIAL = 2
SERVICE_RELAX = 2

def register(client):
    return {"groom": cmd_groom}

async def cmd_groom(client, message, arg):
    city = arg or "Helsinki"
    loc_times = await get_times_for_date(helsinki_date_now(), city)
    location_infos = list(map(build_location_time_message, loc_times.items()))

    if not location_infos:
        await message.channel.send("No parturs found")
        return

    for msg in split_message_for_sending(location_infos, join_str="\n\n"):
        await message.channel.send(msg)

def build_location_time_message(loc_times):
    loc, times = loc_times
    today, tomorrow = times
    text = loc
    if today: text += "\nTänään " + ", ".join(today)
    if tomorrow: text += "\nHuomenna " + ", ".join(tomorrow)
    return text

def split_message_for_sending(pieces, join_str="\n", limit=2000):
    joined = join_str.join(pieces)
    if len(joined) <= limit:
        return [joined]

    a, b = split_list(pieces)
    return [
        *split_message_for_sending(a, join_str, limit),
        *split_message_for_sending(b, join_str, limit),
    ]

def split_list(xs):
    mid = len(xs) // 2
    return xs[:mid], xs[mid:]

async def get_times_for_date(date, city):
    result = {}
    for loc in await get_locations(city):
        today = await get_times(date, loc["url_text"])
        tomorrow = await get_times(date + datetime.timedelta(days=1), loc["url_text"])
        if today or tomorrow:
            result[loc["name"]] = (today, tomorrow)
    return result

@cache.cache(ttl = cache.WEEK)
async def get_locations(city=None):
    json = await call_api("/locations")
    locations = json.get("data", [])
    return list(filter(match_city(city), locations))

def match_city(city):
    return lambda l: city is None or l["city"].lower() == city.lower()

@cache.cache(ttl = cache.HOUR)
async def get_times(date, location):
    assert isinstance(date, datetime.date)
    date_str = date.strftime("%Y-%m-%d")
    params = {"worker_id": "0", "date": date_str, "search_next_date": "true"}
    json = await call_api(f"/locations/{location}/views/palvelut/services/{SERVICE_BASIC}/available", params=params)
    days = json.get("data", [])
    today = next(filter(lambda d: d["date"] == date_str, days), {})
    avail = today.get("available", [])
    return list(a["from"] for a in avail)

async def call_api(path, *, params=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.varaaheti.fi/groom/fi/api/public{path}", params=params) as r:
            log.debug("%s %s %s %s", r.method, r.url, r.status, await r.text())
            if r.status != 200:
                raise Exception(f"Unexpected HTTP status {r.status}")
            return await r.json()

def helsinki_date_now():
    return to_helsinki(as_utc(datetime.datetime.now())).date()
