import asyncio
import json
import os
import traceback

import aiohttp

import database as db
import util

async def get(path):
    headers = {
        "Authorization": "Bot %s" % os.environ["LEMONBOT_TOKEN"],
    }
    url = "https://discordapp.com/api/%s" % path

    async with aiohttp.get(url, headers=headers) as r:
        if r.status == 429:
            body = await r.json()
            print("Hit ratelimit for path: %s", path)
            print(body)
            await asyncio.sleep(body["retry_after"] / 1000.0)
            return await get(path)

        return await r.json()

async def get_messages(channel_id, after):
    return await get("channels/%s/messages?after=%s&limit=100" % (channel_id, after))

async def get_channels(guild_id):
    return await get("guilds/%s/channels" % guild_id)

async def get_user_guilds(user_id):
    return await get("users/%s/guilds" % user_id)

async def fetch_messages_from(channel_id, after_id):
    all_messages = []
    next_messages = await get_messages(channel_id, after_id)

    while len(next_messages) > 0:
        all_messages = next_messages + all_messages
        last_id = next_messages[0]["id"]
        next_messages = await get_messages(channel_id, last_id)

    return all_messages

async def upsert_message(c, message):
    await _upsert_message(c, message, "DO UPDATE SET ts = EXCLUDED.ts, content = EXCLUDED.content, m = EXCLUDED.m")

async def insert_message(c, message):
    await _upsert_message(c, message, "DO NOTHING")

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

async def _upsert_message(c, message, upsert_clause):
    sql = """
        INSERT INTO message
        (message_id, ts, content, m)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (message_id)
        {upsert_clause}
    """.format(upsert_clause=upsert_clause)

    await c.execute(sql, message["id"], parse_ts(message["timestamp"]), message["content"], json.dumps(message))

async def latest_message_id(c, channel_id):
    latest_id = await c.fetchval("SELECT message_id FROM channel_archiver_status WHERE channel_id = $1", channel_id)
    if latest_id is None:
        latest_id = "0"
    return latest_id

async def update_latest_message_id(c, channel_id, message_id):
    await c.execute("""
        INSERT INTO channel_archiver_status
        (channel_id, message_id)
        VALUES ($1, $2)
        ON CONFLICT (channel_id)
        DO UPDATE SET message_id = EXCLUDED.message_id
    """, channel_id, message_id)

async def archive_channel(channel_id):
    async with db.connect() as c:
        latest_id = await latest_message_id(c, channel_id)
        all_messages = await fetch_messages_from(channel_id, latest_id)
        if len(all_messages) > 0:
            for message in all_messages:
                await upsert_message(c, message)

            new_latest_id = all_messages[0]["id"]
            await update_latest_message_id(c, channel_id, new_latest_id)

        print("Fetched total %s messages" % len(all_messages))


async def archive_guild(guild_id):
    channels = await get_channels(guild_id)
    text_channels = list(filter(lambda c: c["type"] == "text", channels))
    print("Archiving %s channels" % len(text_channels))

    for channel in text_channels:
        print("Archiving channel #%s" % channel["name"])
        await archive_channel(channel["id"])

async def run_archival():
    guilds = await get_user_guilds("@me")
    for guild in guilds:
        print("Archiving guild %s" % guild["name"])
        await archive_guild(guild["id"])

async def task(client):
    # Wait until the client is ready
    util.threadsafe(client, client.wait_until_ready())

    # Store new messages every 15 minutes
    while True:
        try:
            await run_archival()
        except Exception:
            await util.log_exception()
        await asyncio.sleep(15 * 60)

def register(client):
    print("archiver: registering")
    util.start_task_thread(task(client))
    return {}
