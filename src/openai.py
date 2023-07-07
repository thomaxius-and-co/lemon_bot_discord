import aiohttp
import asyncio
import discord
import os
import json
import io
import emoji

import http_util
import logger
import retry
import database as db
import util

log = logger.get("OPENAI")

OPENAI_KEY = os.environ.get("OPENAI_KEY", None)
AUTH_HEADER = {"Authorization": "Bearer {0}".format(OPENAI_KEY)}

def is_enabled():
    return OPENAI_KEY is not None

def register(client):
    if not is_enabled():
        log.info("OpenAI feature disabled")
        return {}

    return {
        'setprompt': cmd_setprompt,
        'genimage': cmd_genimage,
    }


async def handle_message(client, message):
    bot_mentioned = any(user for user in message.mentions if user.id == client.user.id)
    if not bot_mentioned:
        return False

    messages = []
    if (systemprompt := await get_channel_prompt(message.channel.id)) is not None:
        messages.append({ "role": "system", "content": systemprompt })
    for m in await get_reply_chain(client, message):
        messages.append({
            "role": "assistant" if m.author.id == client.user.id else "user",
            "content": m.clean_content,
        })
    messages.append({ "role": "user", "content": message.clean_content })

    match await get_response_for_messages(messages):
        case 400, _:
            await message.add_reaction(emoji.CROSS_MARK)
        case 200, result:
            response = result["choices"][0]["message"]["content"]
            reply_target = message
            for msg in util.split_message_for_sending(response.split("\n")):
                reply_target = await reply_target.reply(msg)
    return True
async def get_reply_chain(client, message):
    if message.reference is None:
        return []

    previous = await resolve_message_reference(client, message.reference)
    if previous is None:
        return []
    return await get_reply_chain(client, previous) + [previous]

async def resolve_message_reference(client, reference):
    if isinstance(reference.resolved, discord.DeletedReferencedMessage):
        log.info("Referenced message is deleted")
        return None

    log.info("Message reference not resolved, looking from cache")
    from_cache = next(iter(m for m in client.cached_messages if m.id == reference.message_id), None)
    if from_cache is not None:
        log.info("Message found in cache")
        return from_cache

    log.info("Not in cache, fetching from API")
    if (channel := client.get_channel(reference.channel_id)) is None:
        log.info("Channel not in cache, fetching from API")
        channel = await client.fetch_channel(reference.channel_id)
    return await channel.fetch_message(reference.message_id)

async def cmd_setprompt(client, message, arg):
    if len(arg) > 0:
        await set_channel_prompt(message.channel.id, arg)
    else:
        await delete_channel_prompt(message.channel.id)


async def cmd_genimage(client, message, prompt):
    match await create_image(prompt):
        case 200, response:
            url = response["data"][0]["url"]
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as imageresponse:
                    img = await imageresponse.read()
                    with io.BytesIO(img) as file:
                        await message.reply(file=discord.File(file, f"{prompt}.png"))
        case 400, response:
            await message.add_reaction(emoji.CROSS_MARK)
            if response["error"]["type"] == "invalid_request_error":
                await message.reply(response["error"]["message"])
        case _:
            await message.add_reaction(emoji.CROSS_MARK)


async def get_channel_prompt(channel_id):
    return await db.fetchval("SELECT systemprompt FROM openaiconfig WHERE channel_id = $1", str(channel_id))


async def set_channel_prompt(channel_id, systemprompt):
    await db.execute("""
            INSERT INTO openaiconfig (channel_id, systemprompt) VALUES ($1, $2)
            ON CONFLICT (channel_id) DO UPDATE SET systemprompt = excluded.systemprompt
        """, str(channel_id), systemprompt)


async def delete_channel_prompt(channel_id):
    await db.execute("DELETE FROM openaiconfig WHERE channel_id = $1", str(channel_id))


async def create_image(prompt):
    return await _call_api("/v1/images/generations", json_body={
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
    })


async def get_response_for_messages(messages):
    return await _call_api("/v1/chat/completions", json_body={
        "model": "gpt-4",
        "messages": messages
    })


@retry.on_any_exception(max_attempts = 1, init_delay = 1, max_delay = 30)
async def _call_api(path, json_body=None, query=None):
    url = "https://api.openai.com{0}{1}".format(path, http_util.make_query_string(query))
    async with aiohttp.ClientSession() as session:
        for ratelimit_delay in retry.jitter(retry.exponential(1, 128)):
            response = await session.post(url, headers=AUTH_HEADER, json=json_body)
            log.info({
                "requestMethod": response.method,
                "requestUrl": str(response.url),
                "responseStatus": response.status,
                "requestBody": json.dumps(json_body),
                "responseBody": await response.text(),
            })

            if response.status == 429:
                log.info(f"Ratelimited, retrying in {round(ratelimit_delay, 1)} seconds")
                await asyncio.sleep(ratelimit_delay)
                continue
            return response.status, await response.json()
