async def exec(log, tx):
    await tx.execute("ALTER TABLE faceit_live_stats DROP COLUMN removed")
