async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE censored_words (
            message_id TEXT NOT NULL REFERENCES message(message_id),
            censored_words TEXT NOT NULL,
            exchannel_id TEXT,
            info_message TEXT
        )
    """)
