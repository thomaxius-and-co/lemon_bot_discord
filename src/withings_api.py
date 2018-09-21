import aiohttp
import functools
import os
import json

import database as db
import http_util
import logger

log = logger.get("WITHINGS_API")

AUTH_HOSTNAME = "account.withings.com"
API_HOSTNAME = "wbsapi.withings.net"

class AccountNotLinkedException(Exception):
    pass

def auto_refresh_token(func):
    """
    Annotation that refreshes access token and retries if needed for functions
    that return raw Withings API responses.
    """
    @functools.wraps(func)
    async def func_with_retry(user_id, *args, **kwargs):
        json = await func(user_id, *args, **kwargs)
        if json['status'] == 401:
            await refresh_access_token(user_id)
            return await func(user_id, *args, **kwargs)
        return json
    return func_with_retry

async def get_tokens(user_id):
    row = await db.fetchrow("SELECT access_token, refresh_token FROM withings_link WHERE user_id = $1", user_id)
    if row is None:
        raise AccountNotLinkedException()
    return row["access_token"], row["refresh_token"]

@auto_refresh_token
async def getdevice(user_id):
    access_token, refresh_token = await get_tokens(user_id)
    params = {"action": "getdevice", "access_token": access_token}
    url = f"https://{API_HOSTNAME}/v2/user{http_util.make_query_string(params)}"
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        log.debug("%s %s %s %s", r.method, str(r.url).replace(access_token, "<REDACTED>"), r.status, await r.text())
        return await r.json(content_type='text/json')

async def refresh_access_token(user_id):
    access_token, refresh_token = await get_tokens(user_id)
    async with aiohttp.ClientSession() as session:
        url = f"https://{AUTH_HOSTNAME}/oauth2/token"
        r = await session.post(url, data={
            "grant_type": "refresh_token",
            "client_id": os.environ.get("WITHINGS_CLIENT_ID"),
            "client_secret": os.environ.get("WITHINGS_CLIENT_SECRET"),
            "refresh_token": refresh_token,
        })
        log.debug("%s %s %s %s", r.method, str(r.url).replace(access_token, "<REDACTED>"), r.status, "<REDACTED>")
        token_response = await r.json(content_type='application/json')
        await upsert_access_token(user_id, token_response)
        return token_response['access_token'], token_response['refresh_token']


async def upsert_access_token(user_id, token_response):
    sql = """
        INSERT INTO withings_link (user_id, access_token, refresh_token, original, changed, created)
        VALUES ($1, $2, $3, $4, current_timestamp, current_timestamp)
        ON CONFLICT (user_id) DO UPDATE SET
            access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            original = EXCLUDED.original,
            changed = current_timestamp
    """
    params = [user_id, token_response['access_token'], token_response['refresh_token'], json.dumps(token_response)]
    return await db.execute(sql, *params)

