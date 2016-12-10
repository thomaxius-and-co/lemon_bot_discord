from asyncio import sleep
from dateutil import parser
import aiohttp
from datetime import datetime
import pytz
import time
import traceback
import re
from bs4 import BeautifulSoup
import discord
from database import connect
import emoji

def initialize_schema():
    with connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS feed (
                feed_id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                last_entry TIMESTAMP DEFAULT current_timestamp,
                channel_id TEXT NOT NULL,
                UNIQUE (url)
            );
        """)

async def check_feeds(client):
    with connect() as c:
        c.execute("SELECT feed_id, url, last_entry, channel_id FROM feed")
        feeds = c.fetchall()

    for id, url, last_entry, channel_id in feeds:
        await process_feed(client, id, url, pytz.utc.localize(last_entry), channel_id)

def parse_rss_item(item):
    title = item.find("title").get_text()
    date = parser.parse(item.find("pubdate").get_text())
    url = ""
    if item.find("guid") and item.find("guid").get_text():
        url = item.find("guid").get_text()
    if item.find("link") and item.find("link").get_text():
        url = item.find("link").get_text()

    return {
        "title": title,
        "date": date,
        "url": url,
    }

def parse_atom_item(item):
    title = item.find("title").get_text()
    date = parser.parse(item.find("updated").get_text())
    url = item.find("link").get("href")

    return {
        "title": title,
        "date": date,
        "url": url,
    }

async def get_feed_xml(url):
    async with aiohttp.get(url) as r:
        if r.status != 200:
            print("ERROR: status {0}".format(r.status))
            return None
        return BeautifulSoup(await r.text(), "lxml")

async def get_new_items(url, since):
    def get_title(xml):
        root = xml.find("channel")
        if root is None:
            root = xml.find("feed")
        return root.find("title").get_text()

    xml = await get_feed_xml(url)
    if xml is None:
        return None, []

    items = list(map(parse_rss_item, xml.find_all('item')))
    if len(items) == 0:
        items = map(parse_atom_item, xml.find_all('entry'))

    return get_title(xml), [item for item in items if item["date"] > since]

def make_embed(item):
    embed = discord.Embed(title = item["title"], url = item["url"])
    embed.set_footer(text=str(item["date"]))
    return embed

async def process_feed(client, id, url, last_entry, channel_id):
    print("feed: processing feed '{0}'".format(url))
    title, new_items = await get_new_items(url, last_entry)
    if len(new_items) > 0:
        # Send messages
        for item in new_items:
            embed = make_embed(item)
            embed.set_author(name=title)
            await client.send_message(discord.Object(id=channel_id), embed=embed)

        # Update last entry
        max_timestamp = max(map(lambda i: i["date"], new_items))
        with connect() as c:
            c.execute("""
                UPDATE feed
                SET last_entry = %s
                WHERE feed_id = %s
            """, [max_timestamp, id])

async def task(client):
    await client.wait_until_ready()

    # Check feeds every minute
    fetch_interval = 60

    while True:
        await sleep(fetch_interval)
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

    x = arg.split(" ", 1)
    if len(x) != 2:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return

    cmd, rest = x
    if cmd == "add":
        await cmd_feed_add(client, message, rest)
    elif cmd == "remove":
        await cmd_feed_remove(client, message, rest)
    else:
        await client.add_reaction(message, emoji.CROSS_MARK)

async def cmd_feed_add(client, message, url):
    # TODO: Check the feed is valid
    # TODO: Find feeds from linked url

    with connect() as c:
        c.execute("INSERT INTO feed (url, channel_id) VALUES (%s, %s)", [url, message.channel.id])

    print("feed: added feed '{0}'".format(url))
    await client.add_reaction(message, emoji.WHITE_HEAVY_CHECK_MARK)


async def cmd_feed_remove(client, message, url):
    if url is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return

    with connect() as c:
        c.execute("DELETE FROM feed WHERE url = %s", [url])

    print("feed: removed feed '{0}'".format(url))
    await client.add_reaction(message, emoji.WHITE_HEAVY_CHECK_MARK)

def register(client):
    print("feed: registering")
    initialize_schema()
    client.loop.create_task(task(client))
    return {
        "feed": cmd_feed,
    }
