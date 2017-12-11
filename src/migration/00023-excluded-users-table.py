async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE excluded_users (
            excluded_user_id TEXT NOT NULL REFERENCES discord_user(user_id),
            added_by_id TEXT NOT NULL REFERENCES discord_user(user_id)
        )
    """)
