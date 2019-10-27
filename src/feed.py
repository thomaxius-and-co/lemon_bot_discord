import aiohttp
import asyncio
from contextlib import suppress
from datetime import datetime
import time
import discord
import feedparser
import io

import database as db
import command
import emoji
import util
import logger
import perf
import retry

log = logger.get("FEED")

def time_to_datetime(struct_time):
    return datetime.fromtimestamp(time.mktime(struct_time))

def get_date(entry):
    if hasattr(entry, "published_parsed"):
        struct_time = entry.published_parsed
    elif hasattr(entry, "created_parsed"):
        struct_time = entry.created_parsed
    elif hasattr(entry, "updated_parsed"):
        struct_time = entry.updated_parsed
    elif hasattr(entry, "expired_parsed"):
        struct_time = entry.expired_parsed

    return time_to_datetime(struct_time)

@perf.time_async("Checking feeds")
async def check_feeds(client):
    feeds = await db.fetch("SELECT feed_id, url, last_entry, channel_id FROM feed")

    for id, url, last_entry, channel_id in feeds:
        await process_feed(client, id, url, last_entry, channel_id)

@retry.on_any_exception(max_attempts = 10, init_delay = 1, max_delay = 10)
async def fetch_feed(url):
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        content = "...snip..." if r.status == 200 else (await r.text())
        log.debug("%s %s %s %s", r.method, r.url, r.status, content)
        body = io.BytesIO(await r.read())
        return feedparser.parse(body, response_headers={'content-location': url})

async def get_new_items(url, since):
    def parse_entry(e):
        return {
            "title": e.title,
            "url": e.links[0].href,
            "date": get_date(e),
        }
    d = await fetch_feed(url)
    if not hasattr(d.feed, 'title'):
      return None

    feed_url = getattr(d.feed, 'link', None)

    new_items = [e for e in map(parse_entry, d.entries) if e["date"] > since]
    return d.feed.title, feed_url, sorted(new_items, key=lambda i: i["date"])

def make_embed(item):
    embed = discord.Embed(title = item["title"], url = item["url"])
    embed.set_footer(text=str(item["date"]))
    return embed

async def process_feed(client, id, url, last_entry, channel_id):
    log.info("Processing feed '{0}'".format(url))
    parsed = await get_new_items(url, last_entry)
    if parsed is None:
      log.info("Feed missing title")
      return

    feed_title, feed_url, new_items = parsed
    if len(new_items) > 0:
        # Send messages
        for item in new_items:
            embed = make_embed(item)
            if feed_url is None:
              embed.set_author(name=feed_title)
            else:
              embed.set_author(name=feed_title, url=feed_url)

            channel = util.threadsafe(client, client.fetch_channel(int(channel_id)))
            util.threadsafe(client, channel.send(embed=embed))

        # Update last entry
        max_timestamp = max(map(lambda i: i["date"], new_items))
        await db.execute("""
            UPDATE feed
            SET last_entry = $1
            WHERE feed_id = $2
        """, max_timestamp, id)

async def task(client):
    # Wait until the client is ready
    util.threadsafe(client, client.wait_until_ready())

    # Check feeds every minute
    fetch_interval = 60

    while True:
        await asyncio.sleep(fetch_interval)
        try:
            log.info("Checking feeds")
            await check_feeds(client)
            log.info("Feed: feeds checked")
        except Exception:
            await util.log_exception(log)

async def cmd_feed(client, message, arg):
    if arg is None:
        await respond(message, emoji.CROSS_MARK)
        return

    subcommands = {
        "list": cmd_feed_list,
        "add": cmd_feed_add,
        "remove": cmd_feed_remove,
    }

    cmd, arg = command.parse(arg, prefix="")
    handler = subcommands.get(cmd, None)
    if handler is None:
        await respond(message, emoji.CROSS_MARK)
        return
    await handler(client, message, arg)

async def cmd_feed_list(client, message, _):
    feeds = await db.fetch("SELECT url FROM feed WHERE channel_id = $1 ORDER BY feed_id", str(message.channel.id))
    msg = "Feeds in this channel:\n" + "\n".join(map(lambda f: f[0], feeds))
    await message.channel.send(msg)

async def cmd_feed_add(client, message, url):
    # TODO: Check the feed is valid
    # TODO: Find feeds from linked url

    await db.execute("INSERT INTO feed (url, channel_id) VALUES ($1, $2)", url, str(message.channel.id))

    log.info("Added feed '{0}'".format(url))
    await respond(message, emoji.WHITE_HEAVY_CHECK_MARK)


async def cmd_feed_remove(client, message, url):
    if url is None:
        await respond(message, emoji.CROSS_MARK)
        return

    await db.execute("DELETE FROM feed WHERE url = $1", url)

    log.info("Removed feed '{0}'".format(url))
    await respond(message, emoji.WHITE_HEAVY_CHECK_MARK)

async def respond(message, reaction):
    try:
        await message.add_reaction(reaction)
    except discord.errors.Forbidden:
        with suppress(discord.errors.Forbidden):
            await message.channel.send(reaction)

def register(client):
    log.info("Registering")
    util.start_task_thread(task(client))
    return {
        "feed": cmd_feed,
    }
