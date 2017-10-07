import asyncio
import os
import json

import command
import database as db
import logger
import osu_api as api
import util

log = logger.get("OSU")

async def cmd_osu(client, message, user):
    user_info = next(await api.user(user), None)

    if not user_info:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    user_line = "{user.username} (#{user.rank}) has {user.pp_rounded} pp and {user.accuracy_rounded}% acc".format(user=user_info)

    scores = await api.user_best(user, 5)
    if not scores:
        await client.send_message(message.channel, "No scores found for user %s" % user)
        return

    plays = []
    for i, play in enumerate(scores):
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

    reply = "**{user_line}**\n```{plays}```".format(user_line=user_line, plays="\n".join(plays))
    await client.send_message(message.channel, reply)

async def check_pps(client):
    users = await db.fetch("SELECT osu_user_id, channel_id, last_pp, last_rank FROM osu_pp")
    for u in users:
        await process_user(client, u)

async def process_user(client, user):
  user_id, channel_id, last_pp, last_rank = user
  u = await api.user_by_id(user_id)
  log.info("Checking player {0} performance".format(u.username))

  if last_pp != u.pp:
    msg = "{username} has received {pp_diff} pp! (Rank {rank_diff})".format(
      username = u.username,
      pp_diff = u.pp - last_pp,
      rank_diff = u.rank - last_rank
    )
    util.threadsafe(client, client.send_message(discord.Object(id=channel_id), msg))
    await db.execute("""
      UPDATE osu_pp
      SET last_pp = $1, last_rank = $2, changed = current_timestamp
      WHERE osu_user_id = $3 AND channel_id = $4
    """, u.pp, u.rank, user_id, channel_id)


async def task(client):
    util.threadsafe(client, client.wait_until_ready())
    fetch_interval = 60

    while True:
        await asyncio.sleep(fetch_interval)
        try:
            log.info("Checking tracked player performance")
            await check_pps(client)
        except Exception:
            await util.log_exception(log)

def register(client):
    util.start_task_thread(task(client))
    return {
        "osu": cmd_osu,
    }
