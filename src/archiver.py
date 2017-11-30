import asyncio
from enum import IntEnum
import json
import os
import traceback
import aiohttp
import database as db
import util
import logger
import perf
import retry

log = logger.get("ARCHIVER")

ERROR_MISSING_ACCESS = 50001

class ChannelType(IntEnum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4

def response_is_error(response):
    return type(response) is dict and 'code' in response

@retry.on_any_exception
async def get(path):
    headers = {
        "Authorization": "Bot %s" % os.environ["LEMONBOT_TOKEN"],
    }
    url = "https://discordapp.com/api/v6/%s" % path

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            log.info("GET %s %s %s", url, r.status, await r.text())
            response = await r.json()
            if r.status == 429:
                log.warn("Hit ratelimit for path: %s", path)
                log.warn(response)
                await asyncio.sleep(float(response["retry_after"]) / 1000.0)
                return await get(path)

            if response_is_error(response):
                return None, response
            else:
                return response, None

@perf.time_async("Fetch discord messages")
async def get_messages(channel_id, after):
    return await get("channels/%s/messages?after=%s&limit=100" % (channel_id, after))

async def get_channels(guild_id):
    response, error = await get("guilds/%s/channels" % guild_id)
    return response

async def get_user_guilds(user_id):
    response, error = await get("users/%s/guilds" % user_id)
    return response

async def fetch_messages_from(channel_id, after_id):
    all_messages = []
    next_messages, error = await get_messages(channel_id, after_id)
    if error:
        if error['code'] == ERROR_MISSING_ACCESS:
            log.warning('tried to archive a channel we no longer have access to')
            return []
        else:
            raise Exception(error)

    while len(next_messages) > 0:
        all_messages = next_messages + all_messages
        last_id = next_messages[0]["id"]
        next_messages, error = await get_messages(channel_id, last_id)
        if error:
            if error['code'] == ERROR_MISSING_ACCESS:
                log.warning('tried to archive a channel we no longer have access to')
                break
            else:
                raise Exception(error)

    return all_messages

async def upsert_message(tx, message):
    await _upsert_message(tx, message, "DO UPDATE SET ts = EXCLUDED.ts, content = EXCLUDED.content, m = EXCLUDED.m")

async def insert_message(tx, message):
    await _upsert_message(tx, message, "DO NOTHING")

def parse_ts(ts):
    """Parses Discord timestamp into datetime accepted by asyncpg"""
    import datetime
    import pytz

    has_ms = ts[19] == '.'
    has_tz = ts[-6] in ['-', '+'] and ts[-3] == ':'


    time_fmt = "%Y-%m-%dT%H:%M:%S"
    if has_ms:
        time_fmt += ".%f"
    if has_tz:
        time_fmt += "%z"

    # Remove the ':' in '+00:00' if it exists because strptime doesn't understand it
    if has_tz:
        ts = ts[:-3] + ts[-2:]
    return datetime.datetime.strptime(ts, time_fmt).astimezone(pytz.utc).replace(tzinfo=None)

async def _upsert_message(tx, message, upsert_clause):
    sql = """
        INSERT INTO message
        (message_id, user_id, bot, ts, content, m)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (message_id)
        {upsert_clause}
    """.format(upsert_clause=upsert_clause)

    bot = message["author"].get("bot", False) != False
    await tx.execute(sql, message["id"], message["author"]["id"], bot, parse_ts(message["timestamp"]), message["content"], json.dumps(message))

async def latest_message_id(tx, channel_id):
    latest_id = await tx.fetchval("SELECT message_id FROM channel_archiver_status WHERE channel_id = $1", channel_id)
    if latest_id is None:
        latest_id = "0"
    return latest_id

async def update_latest_message_id(tx, channel_id, message_id):
    await tx.execute("""
        INSERT INTO channel_archiver_status
        (channel_id, message_id)
        VALUES ($1, $2)
        ON CONFLICT (channel_id)
        DO UPDATE SET message_id = EXCLUDED.message_id
    """, channel_id, message_id)

async def archive_channel(channel_id):
    async with db.transaction() as tx:
        latest_id = await latest_message_id(tx, channel_id)
        all_messages = await fetch_messages_from(channel_id, latest_id)
        if len(all_messages) > 0:
            for message in all_messages:
                await upsert_message(tx, message)

            new_latest_id = all_messages[0]["id"]
            await update_latest_message_id(tx, channel_id, new_latest_id)

        log.info("Fetched total %d messages", len(all_messages))

async def archive_guild(guild_id):
    channels = await get_channels(guild_id)
    text_channels = list(filter(lambda c: c["type"] == ChannelType.GUILD_TEXT, channels))
    log.info("Archiving %d channels", len(text_channels))

    for channel in text_channels:
        log.info("Archiving channel #%s", channel["name"])
        await archive_channel(channel["id"])

async def run_archival():
    guilds = await get_user_guilds("@me")
    for guild in guilds:
        log.info("Archiving guild %s", guild["name"])
        await archive_guild(guild["id"])

async def main():
    # Store new messages every 15 minutes
    while True:
        try:
            log.info("Starting archival")
            await run_archival()
        except Exception:
            await util.log_exception(log)
        await asyncio.sleep(15 * 60)

if __name__ == '__main__':
    logger.init()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
