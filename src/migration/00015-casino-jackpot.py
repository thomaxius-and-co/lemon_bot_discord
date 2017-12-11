async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE casino_jackpot (
            jackpot NUMERIC NOT NULL DEFAULT 0
        );

        CREATE TABLE casino_jackpot_history (
            user_id TEXT NOT NULL,
            jackpot NUMERIC NOT NULL DEFAULT 0,
            date NUMERIC NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );

        INSERT INTO casino_jackpot (jackpot) VALUES (0);
    """)

