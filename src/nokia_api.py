import aiohttp
import functools

import http_util
import logger

log = logger.get("NOKIA_API")

def auto_refresh_token(func):
    """
    Annotation that refreshes access token and retries if needed for functions
    that return raw Nokia Health API responses
    """
    @functools.wraps(func)
    async def func_with_retry(user_id, access_token, refresh_token, *args, **kwargs):
        json = await func(user_id, access_token, refresh_token, *args, **kwargs)
        if json['status'] == 401:
            token_response = await refresh_access_token(user_id, access_token, refresh_token)
            new_access_token = token_response['access_token']
            new_refresh_token = token_response['refresh_token']
            return func(user_id, new_access_token, new_refresh_token, *args, **kwargs)
        return json
    return func_with_retry

@auto_refresh_token
async def getdevice(user_id, access_token, refresh_token):
    params = {"action": "getdevice", "access_token": access_token}
    url = "https://api.health.nokia.com/v2/user{0}".format(http_util.make_query_string(params))
    async with aiohttp.ClientSession() as session:
        r = await session.get(url)
        log.info("%s %s %s %s", r.method, str(r.url).replace(access_token, "<REDACTED>"), r.status, await r.text())
        return await r.json(content_type='text/json')

async def refresh_access_token(user_id, access_token, refresh_token):
    async with aiohttp.ClientSession() as session:
        url = "https://account.health.nokia.com/oauth2/token"
        r = await session.post(url, data={
            "grant_type": "refresh_token",
            "client_id": os.environ.get("NOKIA_HEALTH_CLIENT_ID"),
            "client_secret": os.environ.get("NOKIA_HEALTH_CLIENT_SECRET"),
            "refresh_token": refresh_token,
        })
        log.info("%s %s %s %s", r.method, str(r.url).replace(access_token, "<REDACTED>"), r.status, await r.text())
        token_response = await r.json(content_type='application/json')
        await upsert_access_token(user_id, token_response)
        return token_response


async def upsert_access_token(user_id, token_response):
    sql = """
        INSERT INTO nokia_health_link (user_id, access_token, refresh_token, original, changed, created)
        VALUES ($1, $2, $3, $4, current_timestamp, current_timestamp)
        ON CONFLICT (user_id) DO UPDATE SET
            access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            original = EXCLUDED.original,
            changed = current_timestamp
    """
    params = [user_id, token_response['access_token'], token_response['refresh_token'], json.dumps(token_response)]
    return await db.execute(sql, *params)

