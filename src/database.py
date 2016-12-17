import os
from contextlib import contextmanager

import threading
import aiopg

schema_migrations = {
    # Initial DB
    1: """
        -- Bot internals
        CREATE TABLE IF NOT EXISTS schema_version (
            version NUMERIC NOT NULL,
            upgraded TIMESTAMP NOT NULL DEFAULT current_timestamp
        );

        CREATE TABLE IF NOT EXISTS start_times (
            ts timestamp NOT NULL,
            message TEXT
        );


        -- Casino
        CREATE TABLE IF NOT EXISTS casino_account (
            discriminator TEXT NOT NULL,
            balance NUMERIC NOT NULL,
            PRIMARY KEY (discriminator)
        );

        CREATE TABLE IF NOT EXISTS casino_bet (
            discriminator TEXT NOT NULL,
            bet NUMERIC NOT NULL,
            PRIMARY KEY (discriminator)
        );


        -- Archiver
        CREATE TABLE IF NOT EXISTS channel_archiver_status (
            channel_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            PRIMARY KEY (channel_id)
        );
        CREATE TABLE IF NOT EXISTS message (
            message_id TEXT NOT NULL,
            m JSONB NOT NULL,
            PRIMARY KEY (message_id)
        );


        -- Feed
        CREATE TABLE IF NOT EXISTS feed (
            feed_id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            last_entry TIMESTAMP DEFAULT current_timestamp,
            channel_id TEXT NOT NULL,
            UNIQUE (url)
        );
    """,

    # Extract message timestamps and content to columns
    2: """
        ALTER TABLE message ADD COLUMN ts TIMESTAMP;
        UPDATE message SET ts = (m->>'timestamp')::timestamp;
        ALTER TABLE message ALTER COLUMN ts SET NOT NULL;

        ALTER TABLE message ADD COLUMN content TEXT;
        UPDATE message SET content = m->>'content';
        ALTER TABLE message ALTER COLUMN content SET NOT NULL;
    """,

    # Remove old and unused start_times table
    3: """
        DROP TABLE start_times;
    """,

    # Add index for faster message content searches
    4: """
        CREATE INDEX message_content_trgm_idx ON message USING GIN (content gin_trgm_ops);
    """,
}

_pool_holder = threading.local()

_connect_string = "host=localhost dbname=%s user=%s password=%s" % (
    os.environ["DATABASE_NAME"],
    os.environ["DATABASE_USERNAME"],
    os.environ["DATABASE_PASSWORD"]
)

async def get_pool():
    global _pool_holder
    pool = getattr(_pool_holder, "pool", None)
    if pool is None:
        pool = await aiopg.create_pool(_connect_string)
        setattr(_pool_holder, "pool", pool)
    return pool

async def close_pool():
    global _pool_holder
    pool = getattr(_pool_holder, "pool", None)
    if pool is not None:
        pool.close()
        await pool.wait_closed()
        setattr(_pool_holder, "pool", None)

class connect:
    def __init__(self, readonly = False):
        self.readonly = readonly

    async def __aenter__(self):
        self.pool = await get_pool()
        self.con = await self.pool.acquire()
        self.con.set_session(readonly=self.readonly)
        self.cursor = await self.con.cursor()
        return self.cursor

    async def __aexit__(self, exc_type, exc, tb):
        self.cursor.close()
        await self.pool.release(self.con)

async def table_exists(c, table_name):
    await c.execute("SELECT * FROM information_schema.tables WHERE table_name = %s", [table_name])
    return bool(c.rowcount)

async def get_current_schema_version(c):
    if await table_exists(c, "schema_version"):
        await c.execute("SELECT max(version) FROM schema_version;")
        result = await c.fetchone()
        return result[0] if result is not None else 0
    else:
        return 0

def new_migrations(version):
    mig_version = lambda m: m[0]
    not_applied = [ m for m in schema_migrations.items() if mig_version(m) > version ]
    if len(not_applied) == 0:
        return [], version

    not_applied = sorted(not_applied, key=mig_version)
    up_to = max(map(mig_version, not_applied))
    return not_applied, up_to

async def initialize_schema():
    async with connect() as c:
        version = await get_current_schema_version(c)
        migrations, new_version = new_migrations(version)

        if len(migrations) > 0:
            for version, sql in migrations:
                print("database: migrating to version {0}".format(version))
                await c.execute(sql)

            await c.execute("INSERT INTO schema_version (version) VALUES (%s)", [new_version])

    print("database: schema is in up to date")
