async def exec(log, tx):
    # Add user_id field to message table and index it
    await tx.execute("""
        ALTER TABLE message ADD COLUMN user_id TEXT;
        UPDATE message SET user_id = m->'author'->>'id';
        CREATE INDEX message_user_id_idx ON message (user_id);
    """)

