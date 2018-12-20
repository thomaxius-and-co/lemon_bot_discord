async def exec(log, tx):

    await tx.execute("""
        CREATE TABLE IF NOT EXISTS legendary_quotes (
            message_id TEXT NOT NULL PRIMARY KEY REFERENCES message (message_id),
            added_by TEXT NOT NULL REFERENCES discord_user (user_id),
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
    """)
