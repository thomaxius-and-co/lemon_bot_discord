import asyncio
import aiohttp
from datetime import datetime
import time
import traceback
import re
from bs4 import BeautifulSoup
import discord
import feedparser
from threading import Thread

from database import connect
import command
import emoji
import util

def time_to_datetime(struct_time):
    return datetime.fromtimestamp(time.mktime(struct_time))

def get_date(entry):
    if hasattr(entry, "published_parsed"):
        sturct_time = entry.published_parsed
    elif hasattr(entry, "created_parsed"):
        sturct_time = entry.created_parsed
    elif hasattr(entry, "updated_parsed"):
        sturct_time = entry.updated_parsed
    elif hasattr(entry, "expred_parsed"):
        sturct_time = entry.expred_parsed

    return time_to_datetime(sturct_time)

async def check_feeds(client):
    async with connect() as c:
        await c.execute("SELECT feed_id, url, last_entry, channel_id FROM feed")
        feeds = await c.fetchall()

    for id, url, last_entry, channel_id in feeds:
        await process_feed(client, id, url, last_entry, channel_id)

def get_new_items(url, since):
    def parse_entry(e):
        return {
            "title": e.title,
            "url": e.links[0].href,
            "date": get_date(e),
        }
    d = feedparser.parse(url)
    new_items = [e for e in map(parse_entry, d.entries) if e["date"] > since]
    return d.feed.title, d.feed.link, sorted(new_items, key=lambda i: i["date"])

def make_embed(item):
    embed = discord.Embed(title = item["title"], url = item["url"])
    embed.set_footer(text=str(item["date"]))
    return embed

async def process_feed(client, id, url, last_entry, channel_id):
    print("feed: processing feed '{0}'".format(url))
    feed_title, feed_url, new_items = get_new_items(url, last_entry)
    if len(new_items) > 0:
        # Send messages
        for item in new_items:
            embed = make_embed(item)
            embed.set_author(name=feed_title, url=feed_url)

            util.threadsafe(client, client.send_message(discord.Object(id=channel_id), embed=embed))

        # Update last entry
        max_timestamp = max(map(lambda i: i["date"], new_items))
        async with connect() as c:
            await c.execute("""
                UPDATE feed
                SET last_entry = %s
                WHERE feed_id = %s
            """, [max_timestamp, id])

async def task(client):
    # Wait until the client is ready
    util.threadsafe(client, client.wait_until_ready())

    # Check feeds every minute
    fetch_interval = 60

    while True:
        await asyncio.sleep(fetch_interval)
        try:
            print("feed: checking feeds")
            await check_feeds(client)
            print("feed: feeds checked")
        except Exception as e:
            print("ERROR: {0}".format(e))
            traceback.print_exc()

async def cmd_feed(client, message, arg):
    if arg is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return

    subcommands = {
        "list": cmd_feed_list,
        "add": cmd_feed_add,
        "remove": cmd_feed_remove,
    }

    cmd, arg = command.parse(arg, prefix="")
    handler = subcommands.get(cmd, None)
    if handler is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return
    await handler(client, message, arg)

async def cmd_feed_list(client, message, _):
    async with connect() as c:
        await c.execute("SELECT url FROM feed WHERE channel_id = %s ORDER BY feed_id", [message.channel.id])
        feeds = await c.fetchall()
    msg = "Feeds in this channel:\n" + "\n".join(map(lambda f: f[0], feeds))
    await client.send_message(message.channel, msg)

async def cmd_feed_add(client, message, url):
    # TODO: Check the feed is valid
    # TODO: Find feeds from linked url

    async with connect() as c:
        await c.execute("INSERT INTO feed (url, channel_id) VALUES (%s, %s)", [url, message.channel.id])

    print("feed: added feed '{0}'".format(url))
    await client.add_reaction(message, emoji.WHITE_HEAVY_CHECK_MARK)


async def cmd_feed_remove(client, message, url):
    if url is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return

    async with connect() as c:
        await c.execute("DELETE FROM feed WHERE url = %s", [url])

    print("feed: removed feed '{0}'".format(url))
    await client.add_reaction(message, emoji.WHITE_HEAVY_CHECK_MARK)

def thread_func(client):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task(client))

def register(client):
    print("feed: registering")
    Thread(target=thread_func, args=(client,)).start()
    return {
        "feed": cmd_feed,
    }
