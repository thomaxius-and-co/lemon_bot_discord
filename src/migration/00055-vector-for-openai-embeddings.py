async def exec(log, tx):
  await tx.execute("CREATE EXTENSION vector")
  await tx.execute("""
    CREATE TABLE openaiembedding (
      message_id text PRIMARY KEY REFERENCES message(message_id),
      embedding vector (1536) NOT NULL
    )
  """)
