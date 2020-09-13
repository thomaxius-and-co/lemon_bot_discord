async def exec(log, tx):
    # Add index for faster message content searches
    await tx.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    await tx.execute("CREATE INDEX message_content_trgm_idx ON message USING GIN (content gin_trgm_ops)")
