async def exec(log, tx):
    # Add additional records to game stats tables
    await tx.execute("""
        ALTER TABLE whosaidit_stats
        ADD COLUMN streak NUMERIC NOT NULL DEFAULT 0;

        ALTER TABLE whosaidit_stats
        ADD COLUMN record NUMERIC NOT NULL DEFAULT 0;
    """)

