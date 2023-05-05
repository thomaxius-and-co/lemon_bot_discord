import aiohttp
import os

import http_util
import logger
import retry

log = logger.get("OPENAI")

OPENAI_KEY = os.environ.get("OPENAI_KEY", None)
AUTH_HEADER = {"Authorization": "Bearer {0}".format(OPENAI_KEY)}

def register(client):
    if OPENAI_KEY is None:
        log.info("OPENAI_KEY not defined, not enabling feature")
        return {}

    return {
        'openai': cmd_openai,
    }

async def cmd_openai(client, message, arg):
    try:
        result = await chat_completions({
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": arg}
            ]
        })
        response = result["choices"][0]["message"]["content"]
        await message.channel.send(response)
    except Exception:
        await util.log_exception(log)
        await message.channel.send("Something went wrong, Tommi pls fix")


# https://platform.openai.com/docs/api-reference/chat/create
async def chat_completions(payload):
    response = await _call_api("/v1/chat/completions", json_body=payload)
    return await response.json()

@retry.on_any_exception(max_attempts = 1, init_delay = 1, max_delay = 30)
async def _call_api(path, json_body=None, query=None):
    url = "https://api.openai.com{0}{1}".format(path, http_util.make_query_string(query))
    async with aiohttp.ClientSession() as session:
        for ratelimit_delay in retry.jitter(retry.exponential(1, 128)):
            response = await session.post(url, headers=AUTH_HEADER, json=json_body)
            log.info("%s %s %s %s", response.method, response.url, response.status, await response.text())
            return response
