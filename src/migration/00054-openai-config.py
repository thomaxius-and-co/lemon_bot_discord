async def exec(log, tx):
  await tx.execute("""
    CREATE TABLE openaiconfig(
      channel_id text PRIMARY KEY,
      systemprompt text NOT NULL
    );
  """)
