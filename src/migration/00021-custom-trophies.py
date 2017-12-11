async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE custom_trophies (
            message_id TEXT NOT NULL REFERENCES message(message_id),
            trophy_name TEXT NOT NULL,
            trophy_conditions TEXT NOT NULL
        );
    """)
