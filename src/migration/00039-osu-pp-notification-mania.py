async def exec(log, tx):
    await tx.execute("ALTER TABLE osu_pp RENAME COLUMN last_pp TO standard_pp")
    await tx.execute("ALTER TABLE osu_pp RENAME COLUMN last_rank TO standard_rank")

    await tx.execute("ALTER TABLE osu_pp ADD COLUMN mania_pp NUMERIC")
    await tx.execute("ALTER TABLE osu_pp ADD COLUMN mania_rank INT")
