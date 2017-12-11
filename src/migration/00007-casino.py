async def exec(log, tx):
    await tx.execute("""
        -- Casino
        CREATE TABLE IF NOT EXISTS casino_account (
            user_id TEXT NOT NULL,
            balance NUMERIC NOT NULL,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS casino_bet (
            user_id TEXT NOT NULL,
            bet NUMERIC NOT NULL,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS casino_stats (
            user_id TEXT NOT NULL,
            wins_bj NUMERIC NOT NULL DEFAULT 0,
            wins_slots NUMERIC NOT NULL DEFAULT 0,
            losses_bj NUMERIC NOT NULL DEFAULT 0,
            ties NUMERIC NOT NULL DEFAULT 0,
            surrenders NUMERIC NOT NULL DEFAULT 0,
            moneyspent_bj  NUMERIC NOT NULL DEFAULT 0,
            moneyspent_slots  NUMERIC NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS whosaidit_stats (
            user_id TEXT NOT NULL,
            correct NUMERIC NOT NULL DEFAULT 0,
            wrong NUMERIC NOT NULL DEFAULT 0,
            moneyspent  NUMERIC NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );
    """)

