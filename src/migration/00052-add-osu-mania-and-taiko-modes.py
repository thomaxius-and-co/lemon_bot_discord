async def exec(log, tx):
  await tx.execute("""
    INSERT INTO osugamemode (osugamemode_id, name) VALUES
    ('TAIKO', 'osu!taiko'),
    ('CATCH', 'osu!catch')
  """)
  for mode in ['TAIKO', 'CATCH']:
    await tx.execute("""
      INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed)
      SELECT osuuser_id, $1, NULL, NULL, current_timestamp FROM osuuser
    """, mode)
