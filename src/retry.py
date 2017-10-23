import logger
import asyncio

log = logger.get("RETRY")

def on_any_exception(func):
    """
    Retries the function call given amount of times if any exception is thrown.
    Initially delays retry for 100 ms and doubles the delay after every attempt
    up to a maximum of 5000 ms.
    """

    async def func_with_retry(*args, **kwargs):
        max_attempts = 5
        init_delay = 0.1
        max_delay = 5.0

        attempts = 0
        delay_seconds = init_delay
        while attempts < max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    # TODO: What should we do?
                    # - Throw the last exception
                    # - Throw a custom exception that wraps all received ones?
                    log.error("{0}.{1} failed {2} retries. Final exception: {1}".format(func.__module__, func.__name__, max_attempts, e))
                    raise e
                else:
                    log.warn("Retrying {0}.{1} in {2} ms (attempt {3})".format(func.__module__, func.__name__, int(delay_seconds * 1000), attempts))
                    await asyncio.sleep(delay_seconds)
                    delay_seconds = min(max_delay, delay_seconds * 2)

    return func_with_retry
