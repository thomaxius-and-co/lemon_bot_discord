import asyncio
import threading

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
