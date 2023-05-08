import aiohttp
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

    def is_relevant_context(m):
        same_channel = m.channel.id == message.channel.id
        from_bot = m.author.id == client.user.id
        from_user = m.author.id == message.author.id
        is_command = m.content.startswith('!')
        return same_channel and (from_bot or from_user) and not is_command

    context_messages = [m for m in client.cached_messages if is_relevant_context(m) and m.id != message.id]
    messages = []
    for m in context_messages[-5:]:
        messages.append({
            "role": "user" if m.author.id == message.author.id else "assistant",
            "content": m.clean_content,
        })
    systemprompt = await db.fetchval("SELECT systemprompt FROM openaiconfig WHERE channel_id = $1", str(message.channel.id))
    if systemprompt is not None:
        # As mentioned in OpenAI chat completion introduction, the gpt-3.5-turbo-0301 model doesn't pay
        # strong attention to system messages so the system prompt is provided as if it was an user prompt.
        # https://platform.openai.com/docs/guides/chat/introduction
        messages.append({ "role": "user", "content": systemprompt })
    messages.append({ "role": "user", "content": message.clean_content })
    response = await get_response_for_messages(messages)
    for msg in util.split_message_for_sending(response.split("\n")):
        await message.reply(msg)
    return True


async def cmd_setprompt(client, message, arg):
    if len(arg) > 0:
        await db.execute("""
            INSERT INTO openaiconfig (channel_id, systemprompt) VALUES ($1, $2)
            ON CONFLICT (channel_id) DO UPDATE SET systemprompt = excluded.systemprompt
        """, str(message.channel.id), arg)
    else:
        await db.execute("DELETE FROM openaiconfig WHERE channel_id = $1", str(message.channel.id))

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
