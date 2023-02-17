async def exec(log, tx):
  await tx.execute("CREATE TABLE cache(key bytea primary key, value bytea, expires_at timestamptz);")
