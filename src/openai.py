import aiohttp
import discord
import os
import json

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
    }


async def handle_message(client, message):
    bot_mentioned = any(user for user in message.mentions if user.id == client.user.id)
    if not bot_mentioned:
        return False

    messages = []
    for m in await get_reply_chain(client, message):
        messages.append({
            "role": "assistant" if m.author.id == client.user.id else "user",
            "content": m.clean_content,
        })
    if (systemprompt := await get_channel_prompt(message.channel.id)) is not None:
        # As mentioned in OpenAI chat completion introduction, the gpt-3.5-turbo-0301 model doesn't pay
        # strong attention to system messages so the system prompt is provided as if it was an user prompt.
        # https://platform.openai.com/docs/guides/chat/introduction
        messages.append({ "role": "user", "content": systemprompt })
    messages.append({ "role": "user", "content": message.clean_content })
    response = await get_response_for_messages(messages)
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
    return await client.get_channel(reference.channel_id).fetch_message(reference.message_id)

async def cmd_setprompt(client, message, arg):
    if len(arg) > 0:
        await set_channel_prompt(message.channel.id, arg)
    else:
        await delete_channel_prompt(message.channel.id)


async def get_channel_prompt(channel_id):
    return await db.fetchval("SELECT systemprompt FROM openaiconfig WHERE channel_id = $1", str(channel_id))


async def set_channel_prompt(channel_id, systemprompt):
    await db.execute("""
            INSERT INTO openaiconfig (channel_id, systemprompt) VALUES ($1, $2)
            ON CONFLICT (channel_id) DO UPDATE SET systemprompt = excluded.systemprompt
        """, str(channel_id), systemprompt)


async def delete_channel_prompt(channel_id):
    await db.execute("DELETE FROM openaiconfig WHERE channel_id = $1", str(channel_id))

async def get_response_for_messages(messages):
    result = await chat_completions({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })
    return result["choices"][0]["message"]["content"]
async def get_simple_response(prompt):
    result = await chat_completions({
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    return result["choices"][0]["message"]["content"]


# https://platform.openai.com/docs/api-reference/chat/create
async def chat_completions(payload):
    response = await _call_api("/v1/chat/completions", json_body=payload)
    return await response.json()

@retry.on_any_exception(max_attempts = 1, init_delay = 1, max_delay = 30)
async def _call_api(path, json_body=None, query=None):
    log.info("%s", json.dumps(json_body))
    url = "https://api.openai.com{0}{1}".format(path, http_util.make_query_string(query))
    async with aiohttp.ClientSession() as session:
        for ratelimit_delay in retry.jitter(retry.exponential(1, 128)):
            response = await session.post(url, headers=AUTH_HEADER, json=json_body)
            log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())
            return response
