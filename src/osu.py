import asyncio
import discord
import os
import json

import command
import database as db
import logger
import osu_api as api
from osu_api import Mode
import util

log = logger.get("OSU")

async def cmd_osu(client, message, user):
    user_info = await api.user(user, Mode.Standard)

    if not user_info:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    user_line = "{user.username} (#{user.rank}) has {user.pp_rounded} pp and {user.accuracy_rounded}% acc".format(user=user_info)

    scores = await api.user_best(user, 5, Mode.Standard)
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
    users = await db.fetch("SELECT osu_user_id, channel_id, standard_pp, standard_rank, mania_pp, mania_rank FROM osu_pp")
    for u in users:
        await process_standard(client, u)
        await process_mania(client, u)


async def process_standard(client, user):
  await process_user(client, user, "standard_pp", "standard_rank", Mode.Standard)

async def process_mania(client, user):
  await process_user(client, user, "mania_pp", "mania_rank", Mode.Mania)

async def process_user(client, user, pp_key, rank_key, mode):
  user_id = user["osu_user_id"]
  channel_id = user["channel_id"]
  last_pp = user[pp_key]
  last_rank = user[rank_key]

  u = await api.user_by_id(user_id, mode)
  log.info("Checking player {0} performance ({1})".format(u.username, mode))

  if u.pp is None or u.rank is None:
    log.info("Player {0} does not have data for game mode {1}".format(u.username, mode))
    return

  if last_pp is None or last_rank is None:
    await update_pp(pp_key, rank_key, u.pp, u.rank, user_id, channel_id)
    return

  pp_diff = u.pp - float(last_pp)
  if abs(pp_diff) >= 0.1:
    modename = "N/A"
    if mode == Mode.Standard:
      modename = "osu!"
    elif mode == Mode.Mania:
      modename = "osu!mania"

    rank_str = ""
    rank_diff = last_rank - u.rank
    if rank_diff != 0:
      rank_str = " Rank " + format_change(rank_diff)

    msg = "**[{modename}]** {username} has received {pp_diff} pp!{rank_str}".format(
      modename = modename,
      username = u.username,
      pp_diff = round(pp_diff, 1),
      rank_str = rank_str
    )
    util.threadsafe(client, client.send_message(discord.Object(id=channel_id), msg))
    await update_pp(pp_key, rank_key, u.pp, u.rank, user_id, channel_id)

def format_change(diff):
  if diff > 0:
    return "+" + str(diff)
  if diff < 0:
    return str(diff)


async def update_pp(pp_key, rank_key, pp, rank, user_id, channel_id):
    sql = """
      UPDATE osu_pp
      SET {pp_key} = $1, {rank_key} = $2, changed = current_timestamp
      WHERE osu_user_id = $3 AND channel_id = $4
    """.format(pp_key=pp_key, rank_key=rank_key)
    await db.execute(sql, pp, rank, user_id, channel_id)

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
