async def exec(log, tx):
    await tx.execute("""
       CREATE TABLE IF NOT EXISTS crypto_transactions (
           id serial,
           user_id TEXT NOT NULL,
           guild_id TEXT NOT NULL,
           amount decimal NOT NULL,
           price decimal NOT NULL,
           coin TEXT NOT NULL,
           action SMALLINT,
           date DATE DEFAULT CURRENT_TIMESTAMP
           );
   """)
