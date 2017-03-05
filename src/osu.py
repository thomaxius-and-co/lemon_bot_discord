import os
import json
import aiohttp

import command
import osu_api as api

async def cmd_osu(client, message, arg):
    if arg is None:
        return

    subcommands = {
        "user": cmd_osu_user,
        "best": cmd_osu_best,
    }

    cmd, arg = command.parse(arg, prefix="")
    handler = subcommands.get(cmd, None)
    if handler is not None:
        await handler(client, message, arg)
    elif cmd:
        await cmd_osu_user(client, message, cmd)

async def cmd_osu_user(client, message, user):
    result = next(await api.user(user), None)
    if not result:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    reply = "{user.username} (#{user.rank}) has {user.pp_rounded} pp and {user.accuracy_rounded}% acc".format(user=result)
    await client.send_message(message.channel, reply)

async def cmd_osu_best(client, message, user):
    results = await api.user_best(user, 5)
    if not results:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    plays = []
    for i, play in enumerate(results):
        bm = await play.beatmap()

        template = "\n".join([
            "{index}. {bm.artist} - {bm.title} [{bm.version}] (★{bm.stars_rounded})",
            "   {mods}{play.rank} {play.accuracy_rounded}% {play.combo}x{full_combo} {play.pp_rounded}pp, {play.score_formatted} score ({play.date})",
        ])
        plays.append(template.format(
            index = i+1,
            bm = bm,
            play = play,
            full_combo = " FC" if play.full_combo else "",
            mods = (play.mods + " ").lstrip(" "),
        ))

    reply = "```%s```" % "\n".join(plays)
    await client.send_message(message.channel, reply)

def register(client):
    return {
        "osu": cmd_osu,
    }
