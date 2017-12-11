async def exec(log, tx):
    # Add table for reminders
    await tx.execute("""
        CREATE TABLE reminder (
            reminder_id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            ts TIMESTAMP NOT NULL,
            text TEXT NOT NULL,
            original_text TEXT NOT NULL,
            reminded BOOL NOT NULL DEFAULT FALSE
        );
    """)
