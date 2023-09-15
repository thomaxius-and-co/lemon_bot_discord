import aiohttp
import asyncio
import discord
import os
import random

import http_util
import logger
import perf
import retry
import util

log = logger.get("KANSALLISGALLERIA")

objects_with_images = []

def is_enabled():
    return False

def register(client):
  if not is_enabled():
    return {}

  return {
    "art": cmd_art,
  }


async def update_data(client):
  log.info("Fetching newest fulldump")
  global objects_with_images
  objects = await call_api("/v1/objects")
  objects_with_images = [o for o in objects if len(o["multimedia"]) > 0]

async def cmd_art(client, message, _):
  global objects_with_images
  if len(objects_with_images) == 0:
    await message.channel.send("Uh oh, we don't have any art with images! Try again later")
    return

  o = random.choice(objects_with_images)
  title = o["title"]
  embed = discord.Embed(
    title=title.get("fi", title.get("en", title.get("sv", ""))),
    url=f"https://www.kansallisgalleria.fi/en/object/{o['objectId']}"
  )
  embed.set_image(url=o["multimedia"][0]["jpg"]["1000"])
  await message.channel.send(embed=embed)

@retry.on_any_exception()
@perf.time_async("KANSALLISGALLERIA_API")
async def call_api(endpoint, params = {}):
    headers = {"x-api-key": os.environ["KANSALLISGALLERIA_API_KEY"]}
    url = "https://www.kansallisgalleria.fi/api%s%s" % (endpoint, http_util.make_query_string(params))
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers=headers)
        log.debug({
          "requestMethod": r.method,
          "requestUrl": str(r.url),
          "responseStatus": r.status,
          "responseBody": await r.text(),
        })
        return await r.json()
