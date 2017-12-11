async def exec(log, tx):
    await tx.execute("""
        ALTER TABLE faceit_guild_players_list
        ADD FOREIGN KEY (message_id) REFERENCES message (message_id)
    """)
