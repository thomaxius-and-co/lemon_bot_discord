async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE faceit_guild_players_list (
            faceit_nickname TEXT NOT NULL,
            faceit_guid TEXT NOT NULL,
            message_id TEXT NOT NULL REFERENCES message(message_id)
        )
    """)
