async def exec(log, tx):
   await tx.execute("""
        CREATE TABLE IF NOT EXISTS faceit_records_config (
            id serial,
            guild_id TEXT NOT NULL,
            reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_by TEXT NOT NULL REFERENCES discord_user (user_id)
            );
    """)
