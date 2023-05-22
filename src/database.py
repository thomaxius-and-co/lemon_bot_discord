import os

import threading
import asyncpg
import logger
import migration

log = logger.get("DATABASE")

# 15 because we have 5 threads and each has own connection pool
# 75 connections should be more than enough for our loads
MIN_CONNECTION_POOL_SIZE = 2
MAX_CONNECTION_POOL_SIZE = 4

_pool_holder = threading.local()

_connect_string = "postgres://%s:%s@%s:%s/%s" % (
    os.environ["DATABASE_USERNAME"],
    os.environ["DATABASE_PASSWORD"],
    os.environ["DATABASE_HOST"],
    os.environ["DATABASE_PORT"],
    os.environ["DATABASE_NAME"]
)

async def get_pool():
    global _pool_holder
    pool = getattr(_pool_holder, "pool", None)
    if pool is None:
        pool = await asyncpg.create_pool(
            _connect_string,
            min_size=MIN_CONNECTION_POOL_SIZE,
            max_size=MAX_CONNECTION_POOL_SIZE,
            setup=setup_connection,
        )
        setattr(_pool_holder, "pool", pool)
    return pool


async def setup_connection(conn):
    request_id = logger._request_id_var.get("bot")
    await conn.execute(f"SET application_name TO '{request_id}'")


async def close_pool():
    global _pool_holder
    pool = getattr(_pool_holder, "pool", None)
    if pool is not None:
        await pool.close()
        setattr(_pool_holder, "pool", None)

# Database API

async def execute(sql, *args):
    pool = await get_pool()
    async with pool.acquire() as con:
        return await con.execute(sql, *args)

async def fetch(sql, *args):
    pool = await get_pool()
    async with pool.acquire() as con:
        return await con.fetch(sql, *args)

async def fetchrow(sql, *args):
    pool = await get_pool()
    async with pool.acquire() as con:
        return await con.fetchrow(sql, *args)

async def fetchval(sql, *args):
    pool = await get_pool()
    async with pool.acquire() as con:
        return await con.fetchval(sql, *args)

async def explain(sql, *params, tx=None):
    db_obj = tx if tx is not None else __import__(__name__)
    rows = await db_obj.fetch("EXPLAIN " + sql, *params)
    return "\n".join(map(lambda r: r["QUERY PLAN"], rows))

class transaction:
    def __init__(self, readonly = False, pool=None):
        self.readonly = readonly
        self.pool = pool
        self.con = None
        self.tx = None

    async def __aenter__(self):
        if self.pool is None:
            self.pool = await get_pool()
        self.con = await self.pool.acquire()
        self.tx = self.con.transaction(readonly=self.readonly, isolation='serializable' if self.readonly else 'read_committed')
        await self.tx.start()
        return self.con

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            await self.tx.rollback()
        else:
            await self.tx.commit()

        await self.pool.release(self.con)


async def initialize_schema():
    # Pool without init function because we can't register vector type handler before
    # the pgvector extension is created which is done here in migrations
    async with asyncpg.create_pool(_connect_string, min_size=1, max_size=1, setup=setup_connection) as pool:
        async with transaction(pool=pool) as tx:
            await migration.run_migrations(tx)
