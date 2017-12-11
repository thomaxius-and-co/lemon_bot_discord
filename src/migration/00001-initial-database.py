async def exec(log, tx):
    await tx.execute("""
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
    """)
