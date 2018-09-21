async def exec(log, tx):
    await tx.execute("ALTER TABLE nokia_health_link RENAME TO withings_link")
