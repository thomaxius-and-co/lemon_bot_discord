async def exec(log, tx):
    # Extract message timestamps and content to columns
    await tx.execute("""
        ALTER TABLE message ADD COLUMN ts TIMESTAMP;
        UPDATE message SET ts = (m->>'timestamp')::timestamp;
        ALTER TABLE message ALTER COLUMN ts SET NOT NULL;

        ALTER TABLE message ADD COLUMN content TEXT;
        UPDATE message SET content = m->>'content';
        ALTER TABLE message ALTER COLUMN content SET NOT NULL;
    """)
