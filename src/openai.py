import aiohttp
import os

import http_util
import logger
import retry

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
        'openai': cmd_openai,
    }

async def cmd_openai(client, message, arg):
    try:
        response = get_simple_response(arg)
        await message.channel.send(response)
    except Exception:
        await util.log_exception(log)
        await message.channel.send("Something went wrong, Tommi pls fix")

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
