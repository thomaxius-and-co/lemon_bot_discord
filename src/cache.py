import functools
import redis
import pickle

import logger

log = logger.get("CACHE")

HOUR = 60 * 60
WEEK = 7 * 24 * HOUR

def make_key(func, args, kwargs):
    args_pickled = pickle.dumps((args, sorted(kwargs.items())), pickle.HIGHEST_PROTOCOL)
    cache_prefix = "_cache:{0}.{1}:".format(func.__module__, func.__name__)
    return cache_prefix.encode("utf-8") + args_pickled

def cache(ttl=None):
    """
    Cache function results to redis. The ttl (time to live) parameter can be
    used to make the cache invalidate in given amount of seconds.
    """

    if ttl is not None and not isinstance(ttl, int):
      raise TypeError("Expected ttl to be an integer or None")

    def wrap_func_with_cache(func):
        @functools.wraps(func)
        async def func_with_cache(*args, **kwargs):
            cache_key = make_key(func, args, kwargs)
            cached = await redis.get_binary(cache_key)
            if cached is not None:
                log.info("get %s", cache_key)
                return pickle.loads(cached)

            result = await func(*args, **kwargs)
            await redis.set(cache_key, pickle.dumps(result), expire=ttl)
            log.info("set %s", cache_key)
            return result
        return func_with_cache
    return wrap_func_with_cache
