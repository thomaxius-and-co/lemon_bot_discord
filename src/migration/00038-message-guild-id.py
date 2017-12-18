async def exec(log, tx):
    await tx.execute("ALTER TABLE message ADD COLUMN guild_id TEXT")
