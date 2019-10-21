import asyncio
import functools
import itertools
import random

import logger

log = logger.get("RETRY")

def on_any_exception(max_attempts = 5, init_delay = 0.1, max_delay = 5.0):
    def wrapper(func):
        """
        Retries the function call given amount of times if any exception is thrown.
        Initially delays retry for 100 ms and doubles the delay after every attempt
        up to a maximum of 5000 ms.
        """

        @functools.wraps(func)
        async def func_with_retry(*args, **kwargs):
            delay_generator = exponential(init_delay, max_delay)
            attempts = 0
            delay_seconds = next(delay_generator)
            while True:
                try:
                    attempts += 1
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempts == max_attempts:
                        log_error(func, attempts, e)
                        raise e
                    log_retry(func, delay_seconds, attempts, e)
                    await asyncio.sleep(delay_seconds)
                    delay_seconds = next(delay_generator)

        return func_with_retry
    return wrapper

def exponential(base, limit):
    for n in itertools.count():
        yield min(base * (2 ** n), limit)

def jitter(gen, low=0.5):
    for x in gen:
        yield random_between(low, 1.0) * x

def random_between(low, high):
    return low + (high - low) * random.random()

def log_error(func, attempt, e):
    fmt = "{0}.{1} failed {2} retries. Final exception: {3}"
    log.warning(fmt.format(func.__module__, func.__name__, attempt, e))

def log_retry(func, delay_seconds, attempt, e):
    fmt = "Retrying {0}.{1} in {2} ms (attempt {3}). Exception:\n{4}"
    log.warning(fmt.format(func.__module__, func.__name__, int(delay_seconds * 1000), attempt, e))
