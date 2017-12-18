async def exec(log, tx):
    await tx.execute("ALTER TABLE channel_archiver_status ADD COLUMN guild_id TEXT")
