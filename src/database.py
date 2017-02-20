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

    # Add table for reminders
    5: """
        CREATE TABLE reminder (
            reminder_id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            ts TIMESTAMP NOT NULL,
            text TEXT NOT NULL,
            original_text TEXT NOT NULL,
            reminded BOOL NOT NULL DEFAULT FALSE
        );
    """,

    # Add index for message date to make statistics queries faster
    6: """
        CREATE INDEX message_ts_date_idx ON message ((ts::date));
    """,

    7: """

        -- Casino
        CREATE TABLE IF NOT EXISTS casino_account (
            user_id TEXT NOT NULL,
            balance NUMERIC NOT NULL,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS casino_bet (
            user_id TEXT NOT NULL,
            bet NUMERIC NOT NULL,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS casino_stats (
            user_id TEXT NOT NULL,
            wins_bj NUMERIC NOT NULL DEFAULT 0,
            wins_slots NUMERIC NOT NULL DEFAULT 0,
            losses_bj NUMERIC NOT NULL DEFAULT 0,
            ties NUMERIC NOT NULL DEFAULT 0,
            surrenders NUMERIC NOT NULL DEFAULT 0,
            moneyspent_bj  NUMERIC NOT NULL DEFAULT 0,
            moneyspent_slots  NUMERIC NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS whosaidit_stats (
            user_id TEXT NOT NULL,
            correct NUMERIC NOT NULL DEFAULT 0,
            wrong NUMERIC NOT NULL DEFAULT 0,
            moneyspent  NUMERIC NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );

    """,

    # Change discriminator to user_id in casino_bets and casino_account
    8: """
        -- Create user_id column in casino_bet and fill it with data
        ALTER TABLE casino_bet ADD COLUMN user_id TEXT;
        UPDATE casino_bet SET user_id = (
          SELECT m->'author'->>'id'
          FROM message
          WHERE concat(m->'author'->>'username', '#', m->'author'->>'discriminator') = discriminator
          LIMIT 1
        );
        ALTER TABLE casino_bet ALTER COLUMN user_id SET NOT NULL;

        -- Change casino_bet primary key from discriminator to user_id
        ALTER TABLE casino_bet DROP CONSTRAINT casino_bet_pkey;
        ALTER TABLE casino_bet ADD PRIMARY KEY (user_id);

        -- Drop discriminator column
        ALTER TABLE casino_bet DROP COLUMN discriminator;

        -- Create user_id column in casino_account and fill it with data
        ALTER TABLE casino_account ADD COLUMN user_id TEXT;
        UPDATE casino_account SET user_id = (
          SELECT m->'author'->>'id'
          FROM message
          WHERE concat(m->'author'->>'username', '#', m->'author'->>'discriminator') = discriminator
          LIMIT 1
        );
        ALTER TABLE casino_bet ALTER COLUMN user_id SET NOT NULL;

        -- Change casino_account primary key from discriminator to user_id
        ALTER TABLE casino_account DROP CONSTRAINT casino_account_pkey;
        ALTER TABLE casino_account ADD PRIMARY KEY (user_id);

        -- Drop discriminator column
        ALTER TABLE casino_account DROP COLUMN discriminator;
    """,

    # Fix incorrect reminder times
    9: """
        UPDATE reminder SET ts = ts - interval '2 hours';
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
