async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE osu_pp (
            osu_pp_id SERIAL PRIMARY KEY,
            osu_user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            last_pp NUMERIC NOT NULL,
            last_rank INT NOT NULL,
            changed TIMESTAMP NOT NULL,
            UNIQUE (osu_user_id, channel_id)
        );
    """)
