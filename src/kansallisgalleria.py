import aiohttp
import asyncio
import discord
import os
import database as db
import random
import tempfile
from contextlib import asynccontextmanager
import json
import json_stream
from json_stream.dump import JSONStreamEncoder

import http_util
import logger
import perf
import retry
import util

log = logger.get("KANSALLISGALLERIA")

def is_enabled():
    return "KANSALLISGALLERIA_API_KEY" in os.environ

def register(client):
  if not is_enabled():
    return {}

  return {
    "art": cmd_art,
  }


@perf.time_async("Kansallisgalleria data import")
async def update_data(client):
  log.info("Fetching newest fulldump")
  with tempfile.TemporaryFile() as file:
    # Write response to file
    async with call_api_raw_stream("/v1/objects") as r:
        async for data in r.content.iter_chunked(4096):
            file.write(data)

    # Read from the file and insert into database
    file.seek(0)
    async with db.transaction() as tx:
        await tx.execute("TRUNCATE kgobject")
        await batch_insert_objects(tx, file)

@perf.time_async("Kansallisgalleria data import - database insert")
async def batch_insert_objects(tx, file):
    batch = []
    for obj in json_stream.load(fp).persistent():
        has_media = len(obj["multimedia"]) > 0
        has_title = "title" in obj and obj["title"] is not None
        if has_title and has_media:
            batch.append((obj["id"], json.dumps(obj, cls=JSONStreamEncoder)))

        if len(batch) >= 1000:
            await tx.executemany("INSERT INTO kgobject (kgobject_id, data) VALUES ($1, $2)", batch)
            batch = []

    # Last batch
    if len(batch) > 0:
        await tx.executemany("INSERT INTO kgobject (kgobject_id, data) VALUES ($1, $2)", batch)
        batch = []

async def cmd_art(client, message, _):
  ids = await db.fetch("select kgobject_id from kgobject")
  if len(ids) == 0:
    await message.channel.send("Uh oh, we don't have any art with images! Try again later")
    return

  random_id = random.choice(ids)["kgobject_id"]
  o = json.loads(await db.fetchval("select data from kgobject where kgobject_id = $1", random_id))
  title = o["title"]
  embed = discord.Embed(
    title=title.get("fi", title.get("en", title.get("sv", ""))),
    url=f"https://www.kansallisgalleria.fi/en/object/{o['id']}"
  )
  multimedia = o["multimedia"][0]
  filename = str(multimedia['id']) + multimedia['filename_extension']
  image_url = f"https://d3uvo7vkyyb63c.cloudfront.net/1/jpg/1000/{filename}"
  embed.set_image(url=image_url)
  await message.channel.send(embed=embed)

@retry.on_any_exception()
@perf.time_async("KANSALLISGALLERIA_API")
async def call_api(endpoint, params = {}):
    async with call_api_raw_stream(endpint, params) as r:
        return await r.json()

#@retry.on_any_exception()
#@perf.time_async("KANSALLISGALLERIA_API")
@asynccontextmanager
async def call_api_raw_stream(endpoint, params = {}):
    headers = {"x-api-key": os.environ["KANSALLISGALLERIA_API_KEY"]}
    url = "https://www.kansallisgalleria.fi/api%s%s" % (endpoint, http_util.make_query_string(params))
    async with aiohttp.ClientSession() as session:
        r = await session.get(url, headers=headers)
        log.debug({
          "requestMethod": r.method,
          "requestUrl": str(r.url),
          "responseStatus": r.status,
        })
        yield r
