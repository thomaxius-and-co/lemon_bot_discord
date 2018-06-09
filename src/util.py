import asyncio
import json
import os
import sys
import threading
import traceback
import aiohttp
import logger

log = logger.get("UTIL")

async def log_exception(error_log):
    err_str = traceback.format_exc()
    error_log.error(err_str)

    # If the error is 'Event loop is closed' we crash the bot and let it restart
    # A retarded solution to a retarded issue
    error_message = str(sys.exc_info()[1])
    if error_message == 'Event loop is closed':
        msg = "Snipety snap! Event loop is closed! Committing sudoku in 3.. 2.. 1.."
        log.error(msg)
        os._exit(0)

# Run discord.py coroutines from antoher thread
def threadsafe(client, coroutine):
    return asyncio.run_coroutine_threadsafe(coroutine, client.loop).result()

# Start a coroutine task in new thread
def start_task_thread(coroutine):
    def thread_func(coroutine):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coroutine)
    threading.Thread(target=thread_func, args=(coroutine,)).start()

async def pmap(async_func, xs):
    futures = map(async_func, xs)
    return await asyncio.gather(*futures)

def grouped(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]
