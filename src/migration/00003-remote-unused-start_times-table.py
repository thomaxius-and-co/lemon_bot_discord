async def exec(log, tx):
    await tx.execute("DROP TABLE start_times")
