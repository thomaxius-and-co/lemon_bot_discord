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

async def user_best(name, limit):
    if not (1 <= limit <= 100):
        raise Error("osu: invalid limit")

    return await call_api("get_user_best", {
        "k": os.environ["OSU_API_KEY"],
        "type": "u",
        "u": name,
        "limit": str(limit),
    })

async def beatmap(id):
    beatmaps = await call_api("get_beatmaps", {
        "k": os.environ["OSU_API_KEY"],
        "m": "0",
        "b": str(id),
        "limit": "1",
    })
    return beatmaps[0] if len(beatmaps) > 0 else None

def format_pp(play):
    return round(float(play["pp"]))

def format_score(play):
    score = int(play["score"])
    if score > 1000000:
        return "%sM" % round(score / 1000000.0, 1)
    if score > 1000:
        return "%sk" % round(score / 1000.0, 1)
    return "%s" % score

def format_accuracy(play):
    hits = 0
    hits += int(play["count50"]) * 50
    hits += int(play["count100"]) * 100
    hits += int(play["count300"]) * 300
    max_hits = (int(play["count50"]) + int(play["count100"]) + int(play["count300"]) + int(play["countmiss"])) * 300
    return round(float(hits) / float(max_hits) * 100, 2)

async def cmd_osu(client, message, arg):
    split = arg.split(" ", 1)
    if len(split) > 1:
        cmd, arg = split
        if cmd == "user":
            await cmd_osu_user(client, message, arg)
        elif cmd == "best":
            await cmd_osu_best(client, message, arg)
        else:
            # error
            pass
    else:
        await cmd_osu_user(client, message, arg)

async def cmd_osu_user(client, message, user):
    results = await user(user)
    if not results:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    data = results[0]
    username = data["username"]
    rank = int(data["pp_rank"])
    pp = round(float(data["pp_raw"]))
    acc = float(data["accuracy"])

    reply = "%s (#%d) has %d pp and %.2f%% acc" % (username, rank, pp, acc)
    await client.send_message(message.channel, reply)

def format_mods(mods):
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
        print(name, mask)
        if mods & mask:
            s += name
    return (s + " ").lstrip(" ")

async def cmd_osu_best(client, message, user):
    results = await user_best(user, 5)
    if not results:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    plays = []
    for i, play in enumerate(results):
        beatmap_id = play["beatmap_id"]
        bm = await beatmap(beatmap_id)
        if bm is not None:
            beatmap_name = "{artist} - {title} [{version}]".format(**bm)
            stars = round(float(bm["difficultyrating"]), 2)
        else:
            beatmap_name = "#" + beatmap_id
            stars = "?.??"

        info = {
            "index": i + 1,
            "beatmap_name": beatmap_name,
            "stars": stars,
            "rank": play["rank"],
            "mods": format_mods(int(play["enabled_mods"])),
            "score": format_score(play),
            "pp": format_pp(play),
            "acc": format_accuracy(play),
            "date": play["date"],
            "combo": int(play["maxcombo"]),
            "fc": "" if play["perfect"] == "0" else " FC",
        }

        template = "\n".join([
            "{index}. {beatmap_name} (★{stars})",
            "   {mods}{rank} {acc}% {combo}x{fc} {pp}pp, {score} score ({date})",
        ])
        plays.append(template.format(**info))

    reply = "```%s```" % "\n".join(plays)
    await client.send_message(message.channel, reply)

def register(client):
    return {
        "osu": cmd_osu,
    }
