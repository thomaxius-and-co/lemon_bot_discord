async def exec(log, tx):
    await tx.execute("ALTER TABLE faceit_guild_players_list ADD COLUMN custom_nickname TEXT")
