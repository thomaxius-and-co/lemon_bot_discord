async def exec(log, tx):
    # Add bot field to message table and index it
    await tx.execute("""
        ALTER TABLE message ADD COLUMN bot BOOL;
        UPDATE message SET bot = coalesce(m->'author'->>'bot', 'false') != 'false';
        CREATE INDEX message_bot_idx ON message (bot);
        ALTER TABLE message ALTER COLUMN bot SET NOT NULL;
    """)
