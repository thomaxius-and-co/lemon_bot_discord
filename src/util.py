import asyncio
import os
import sys
import threading
import traceback
import logger

log = logger.get("UTIL")

async def log_exception(error_log, msg=None):
    err_str = traceback.format_exc()
    if msg is not None:
        err_str = msg + "\n" + err_str
    error_log.error(err_str)

    # If the error is 'Event loop is closed' we crash the bot and let it restart
    # A retarded solution to a retarded issue
    error_message = str(sys.exc_info()[1])
    if error_message == 'Event loop is closed':
        msg = "Snipety snap! Event loop is closed! Committing sudoku in 3.. 2.. 1.."
        log.error(msg)
        os._exit(0)


async def pmap(async_func, xs):
    futures = map(async_func, xs)
    return await asyncio.gather(*futures)


def grouped(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]


def split_list(xs):
    mid = len(xs) // 2
    return xs[:mid], xs[mid:]


def split_message_for_sending(pieces: str, join_str="\n", limit=2000):
    joined = join_str.join(pieces)
    if len(joined) <= limit:
        return [joined]

    a, b = split_list(pieces)
    return [
        *split_message_for_sending(a, join_str, limit),
        *split_message_for_sending(b, join_str, limit),
    ]