async def exec(log, tx):
    await tx.execute("ALTER TABLE faceit_guild_players_list ADD COLUMN deleted BOOL NOT NULL DEFAULT FALSE")
