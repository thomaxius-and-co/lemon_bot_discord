async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE whosaidit_weekly_winners (
            user_id TEXT NOT NULL REFERENCES discord_user(user_id),
            wins NUMERIC NOT NULL DEFAULT 0,
            losses NUMERIC NOT NULL DEFAULT 0,
            time timestamp NOT NULL
        );
    """)

