async def exec(log, tx):
    # Database table for storing precalculated statistics
    await tx.execute("""
        CREATE TABLE statistics (
            statistics_id TEXT PRIMARY KEY,
            content JSONB NOT NULL,
            changed TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)
