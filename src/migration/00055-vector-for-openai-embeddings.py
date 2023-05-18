async def exec(log, tx):
  # These fail if run without the extension installed which
  # means these migrations can't be run on a fresh database
  # without the now unnecessary pgvector extension
  return

  await tx.execute("CREATE EXTENSION vector")
  await tx.execute("""
    CREATE TABLE openaiembedding (
      message_id text PRIMARY KEY REFERENCES message(message_id),
      embedding vector (1536) NOT NULL
    )
  """)
