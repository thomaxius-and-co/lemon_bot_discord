async def exec(log, tx):
    # Create table for user information
    await tx.execute("""
        CREATE TABLE discord_user (
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            raw JSONB NOT NULL,
            PRIMARY KEY (user_id)
        );
    """)

