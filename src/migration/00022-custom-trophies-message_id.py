async def exec(log, tx):
    await tx.execute("""
        ALTER TABLE custom_trophies
        ADD FOREIGN KEY (message_id) REFERENCES message (message_id)
    """)
