async def exec(log, tx):
  await tx.execute("""
      CREATE TABLE kgobject (
        kgobject_id bigint PRIMARY KEY,
        data JSONB NOT NULL
      );
  """)