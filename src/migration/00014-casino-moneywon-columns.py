async def exec(log, tx):
    await tx.execute("""
        ALTER TABLE casino_stats
        ADD COLUMN moneywon_bj NUMERIC NOT NULL DEFAULT 0;

        ALTER TABLE casino_stats
        ADD COLUMN moneywon_slots NUMERIC NOT NULL DEFAULT 0;
    """)

