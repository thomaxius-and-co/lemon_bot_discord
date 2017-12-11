async def exec(log, tx):
    await tx.execute("""
        ALTER TABLE censored_words
        ADD FOREIGN KEY (message_id) REFERENCES message (message_id);
    """)
