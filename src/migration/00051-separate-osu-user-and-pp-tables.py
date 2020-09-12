async def exec(log, tx):
  await tx.execute("""
    CREATE TABLE osugamemode (
      osugamemode_id TEXT PRIMARY KEY,
      name TEXT NOT NULL
    )
  """)
  await tx.execute("""
    INSERT INTO osugamemode (osugamemode_id, name) VALUES
    ('STANDARD', 'osu!standard'),
    ('MANIA', 'osu!mania')
  """)
  await tx.execute("""
    CREATE TABLE osuuser (
      osuuser_id TEXT NOT NULL,
      channel_id TEXT NOT NULL,
      PRIMARY KEY (osuuser_id, channel_id)
    );
  """)
  await tx.execute("""
    CREATE TABLE osupp (
      osuuser_id TEXT NOT NULL,
      osugamemode_id TEXT NOT NULL REFERENCES osugamemode (osugamemode_id),
      pp NUMERIC NOT NULL,
      rank INT NOT NULL,
      changed TIMESTAMP NOT NULL,
      PRIMARY KEY (osuuser_id, osugamemode_id)
    );
  """)
  await tx.execute("""
    INSERT INTO osuuser (osuuser_id, channel_id)
    SELECT osu_user_id, channel_id FROM osu_pp
  """)
  await tx.execute("""
    INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed)
    SELECT osu_user_id, 'STANDARD', standard_pp, standard_rank, changed FROM osu_pp
  """)
  await tx.execute("""
    INSERT INTO osupp (osuuser_id, osugamemode_id, pp, rank, changed)
    SELECT osu_user_id, 'MANIA', mania_pp, mania_rank, changed FROM osu_pp
  """)
  await tx.execute("DROP TABLE osu_pp")
