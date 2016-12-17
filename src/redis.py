import aioredis
import os
import threading

_connection_pools = {}

def connection_details():
    return (os.environ["REDIS_HOST"], int(os.environ["REDIS_PORT"]))

async def get_pool():
    global _connection_pools
    thread_id = threading.get_ident()
    pool = _connection_pools.get(thread_id, None)
    if pool is None:
        pool = await aioredis.create_pool(connection_details())
        _connection_pools[thread_id] = pool
    return pool

async def close_pool():
    global _connection_pools
    thread_id = threading.get_ident()
    pool = _connection_pools.get(thread_id, None)
    if pool is not None:
        pool.close()
        await pool.wait_closed()
        del _connection_pools[thread_id]

class connect:
    def __init__(self):
        pass

    async def __aenter__(self):
        self.pool = await get_pool()
        self.redis = await self.pool.acquire()
        return self.redis

    async def __aexit__(self, exc_type, exc, tb):
        self.pool.release(self.redis)
        self.redis = None
