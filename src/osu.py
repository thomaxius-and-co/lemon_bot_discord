import asyncio
from asyncpg.exceptions import UniqueViolationError
import aiohttp

import command
import database as db
import logger
import osu_api as api
from osu_api import Mode
import util

log = logger.get("OSU")


async def cmd_osu(client, message, user):
    cmd, arg = command.parse(user, prefix="")
    if cmd == "add":
        return await cmd_osu_add(client, message, arg)
    elif cmd in ["rm", "remove", "delete", "del"]:
        return await cmd_osu_remove(client, message, arg)

    user_info = await api.user(user, Mode.Standard)

    if not user_info:
        await message.channel.send("User %s not found" % user)
        return

    user_line = "{user.username} (#{user.rank}) has {user.pp_rounded} pp and {user.accuracy_rounded}% acc".format(user=user_info)

    scores = await api.user_best(user, 5, Mode.Standard)
    if not scores:
        await message.channel.send("No scores found for user %s" % user)
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
    await message.channel.send(reply)

async def cmd_osu_add(client, message, arg):
    user = arg.strip()
    if not user: return

    log.info(f"Adding osu player '{user}' by user {message.author.id} ({message.author.name})")
    user_std = await api.user(user, Mode.Standard)
    user_taiko = await api.user(user, Mode.Taiko)
    user_catch = await api.user(user, Mode.Catch)
    user_mania = await api.user(user, Mode.Mania)
    if not user_std or not user_taiko or not user_catch or not user_mania:
        return await message.channel.send("User could not be found")

    try:
        async with db.transaction() as tx:
          await tx.execute("INSERT INTO osuuser (osuuser_id, channel_id) VALUES ($1, $2)", user_std.id, str(message.channel.id))
          await tx.execute("INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed) VALUES ($1, 'STANDARD', $2, $3, current_timestamp)", user_std.id, user_std.pp, user_std.rank)
          await tx.execute("INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed) VALUES ($1, 'TAIKO', $2, $3, current_timestamp)", user_taiko.id, user_taiko.pp, user_taiko.rank)
          await tx.execute("INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed) VALUES ($1, 'CATCH', $2, $3, current_timestamp)", user_catch.id, user_catch.pp, user_catch.rank)
          await tx.execute("INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed) VALUES ($1, 'MANIA', $2, $3, current_timestamp)", user_mania.id, user_mania.pp, user_mania.rank)
    except UniqueViolationError:
        return await message.channel.send(f"User is already added")

async def cmd_osu_remove(client, message, arg):
    user = arg.strip()
    if not user: return

    log.info(f"Deleting osu player '{user}' by user {message.author.id} ({message.author.name})")

    user_std = await api.user(user, Mode.Standard)
    async with db.transaction() as tx:
      await tx.execute("DELETE FROM osupp WHERE osuuser_id = $1", user_std.id)
      await tx.execute("DELETE FROM osuuser WHERE osuuser_id = $1", user_std.id)

async def check_pps(client):
    users = await db.fetch("""
      SELECT
        osuuser.osuuser_id, channel_id,
        standard.pp AS standard_pp, standard.rank AS standard_rank,
        taiko.pp AS taiko_pp, taiko.rank AS taiko_rank,
        catch.pp AS catch_pp, catch.rank AS catch_rank,
        mania.pp AS mania_pp, mania.rank AS mania_rank
      FROM osuuser
      LEFT JOIN osupp standard ON (osuuser.osuuser_id = standard.osuuser_id AND standard.osugamemode_id = 'STANDARD')
      LEFT JOIN osupp taiko ON (osuuser.osuuser_id = taiko.osuuser_id AND taiko.osugamemode_id = 'TAIKO')
      LEFT JOIN osupp catch ON (osuuser.osuuser_id = catch.osuuser_id AND catch.osugamemode_id = 'CATCH')
      LEFT JOIN osupp mania ON (osuuser.osuuser_id = mania.osuuser_id AND mania.osugamemode_id = 'MANIA')
    """)
    for u in users:
      try:
        await process_standard(client, u)
        await process_taiko(client, u)
        await process_catch(client, u)
        await process_mania(client, u)
      except aiohttp.client_exceptions.ContentTypeError:
        log.warning("osu! API responded with whatever non-json garbage :shrug:")


async def process_standard(client, user):
  await process_user(client, user, Mode.Standard, user["standard_pp"], user["standard_rank"])

async def process_taiko(client, user):
  await process_user(client, user, Mode.Taiko, user["taiko_pp"], user["taiko_rank"])

async def process_catch(client, user):
  await process_user(client, user, Mode.Catch, user["catch_pp"], user["catch_rank"])

async def process_mania(client, user):
  await process_user(client, user, Mode.Mania, user["mania_pp"], user["mania_rank"])

async def process_user(client, user, mode, last_pp, last_rank):
  user_id = user["osuuser_id"]
  channel_id = user["channel_id"]

  u = await api.user_by_id(user_id, mode)
  log.info("Checking player {0} performance ({1})".format(u.username, mode))

  if u.pp is None or u.rank is None:
    log.info("Player {0} does not have data for game mode {1}".format(u.username, mode))
    return

  if last_pp is None or last_rank is None:
    await update_pp(user_id, mode, u.pp, u.rank)
    return

  pp_diff = u.pp - float(last_pp)
  if abs(pp_diff) >= 0.1:
    modename = "N/A"
    if mode == Mode.Standard:
      modename = "osu!"
    elif mode == Mode.Taiko:
        modename = "osu!taiko"
    elif mode == Mode.Catch:
        modename = "osu!catch"
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
    channel = await client.fetch_channel(int(channel_id))
    await channel.send(msg)
    await update_pp(user_id, mode, u.pp, u.rank)

def format_change(diff):
  if diff > 0:
    return "+" + str(diff)
  if diff < 0:
    return str(diff)


def mode_to_gamemode_id(mode: Mode) -> str:
  return {
    Mode.Mania: "MANIA",
    Mode.Taiko: "TAIKO",
    Mode.Catch: "CATCH",
    Mode.Standard: "STANDARD",
  }[mode]

async def update_pp(user_id, mode, pp, rank):
  gamemode_id = mode_to_gamemode_id(mode)
  await db.execute("""
    UPDATE osupp
    SET pp = $1, rank = $2, changed = current_timestamp
    WHERE osuuser_id = $3 AND osugamemode_id = $4
  """, pp, rank, user_id, gamemode_id)

async def task(client):
    fetch_interval = 10 * 60

    while True:
        await asyncio.sleep(fetch_interval)
        try:
            log.info("Checking tracked player performance")
            await check_pps(client)
        except Exception:
            await util.log_exception(log)

def register(client):
    return {
        "osu": cmd_osu,
    }
