async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE whosaidit_stats_history (
            user_id TEXT NOT NULL REFERENCES discord_user(user_id),
            message_id TEXT NOT NULL REFERENCES message(message_id),
            quote TEXT NOT NULL,
            correctname TEXT NOT NULL,
            playeranswer TEXT NOT NULL,
            correct NUMERIC NOT NULL DEFAULT 0,
            streak NUMERIC NOT NULL DEFAULT 0,
            losestreak NUMERIC NOT NULL DEFAULT 0,
            time timestamp NOT NULL,
            week NUMERIC NOT NULL
        );
    """)

