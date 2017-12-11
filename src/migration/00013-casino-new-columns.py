async def exec(log, tx):
    await tx.execute("""
        ALTER TABLE casino_stats
        ADD COLUMN losses_slots NUMERIC NOT NULL DEFAULT 0;

        ALTER TABLE casino_stats
        ADD COLUMN biggestwin_slots NUMERIC NOT NULL DEFAULT 0;

        ALTER TABLE casino_stats
        ADD COLUMN bj_blackjack NUMERIC NOT NULL DEFAULT 0;
    """)
