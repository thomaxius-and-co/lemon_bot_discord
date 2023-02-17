import functools
import database as db
import pickle

import logger

log = logger.get("CACHE")

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY

def make_key(func, args, kwargs):
    args_pickled = pickle.dumps((args, sorted(kwargs.items())), pickle.HIGHEST_PROTOCOL)
    cache_prefix = "_cache:{0}.{1}:".format(func.__module__, func.__name__)
    return cache_prefix.encode("utf-8") + args_pickled

async def get_binary(cache_key):
    sql = "SELECT value FROM cache WHERE key = $1 AND (expires_at > current_timestamp OR expires_at IS NULL)"
    return await db.fetchval(sql, cache_key)
async def set(cache_key, value, expire):
    sql = """
        INSERT INTO cache (key, value, expires_at) VALUES ($1, $2, current_timestamp + ($3 || ' seconds')::interval)
        ON CONFLICT (key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
    """
    return await db.execute(sql, cache_key, value, str(expire))

def cache(ttl=None):
    """
    Cache function results to database. The ttl (time to live) parameter can be
    used to make the cache invalidate in given amount of seconds.
    """

    if ttl is not None and not isinstance(ttl, int):
      raise TypeError("Expected ttl to be an integer or None")

    def wrap_func_with_cache(func):
        @functools.wraps(func)
        async def func_with_cache(*args, **kwargs):
            cache_key = make_key(func, args, kwargs)
            cached = await get_binary(cache_key)
            if cached is not None:
                log.debug("GET %s", cache_key)
                return pickle.loads(cached)

            result = await func(*args, **kwargs)
            await set(cache_key, pickle.dumps(result), expire=ttl)
            log.debug("SET %s", cache_key)
            return result
        return func_with_cache
    return wrap_func_with_cache
