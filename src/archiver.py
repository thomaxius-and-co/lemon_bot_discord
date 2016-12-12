import asyncio
import json
import os

import aiohttp

import database as db

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

def insert_message(c, message):
    sql = """
        INSERT INTO message
        (message_id, ts, content, m)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (message_id)
        DO UPDATE SET
            m = EXCLUDED.m
    """
    c.execute(sql, [
        message["id"],
        message["timestamp"],
        message["content"],
        json.dumps(message),
    ])


async def archive_channel(channel_id):
    with db.connect() as c:
        c.execute("""
            INSERT INTO channel_archiver_status
            (channel_id, message_id)
            VALUES (%s, '0')
            ON CONFLICT DO NOTHING;
        """, [channel_id])
        c.execute("SELECT message_id FROM channel_archiver_status WHERE channel_id = %s", [channel_id])
        latest_id = c.fetchone()[0]
        all_messages = await fetch_messages_from(channel_id, latest_id)
        if len(all_messages) > 0:
            new_latest_id = all_messages[0]["id"]

            c.execute("""
                UPDATE channel_archiver_status
                SET message_id = %s
                WHERE channel_id = %s
            """, [new_latest_id, channel_id])


            for message in all_messages:
                insert_message(c, message)

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
    await client.wait_until_ready()

    # Store new messages every 15 minutes
    while True:
        try:
            await run_archival()
        except Exception as e:
            print("Archival failed:")
            print(e)
        await asyncio.sleep(15 * 60)

def register(client):
    client.loop.create_task(task(client))
    return {}
