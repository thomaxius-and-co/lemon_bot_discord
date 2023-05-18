async def exec(log, tx):
  await tx.execute("DROP TABLE IF EXISTS openaiembedding")
  await tx.execute("DROP EXTENSION IF EXISTS vector")
