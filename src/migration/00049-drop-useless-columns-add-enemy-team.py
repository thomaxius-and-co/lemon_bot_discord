async def exec(log, tx):
   await tx.execute("""
         ALTER TABLE faceit_records
         DROP COLUMN match_length_seconds,
         DROP COLUMN dpr_ratio
    """)
   await tx.execute("""
         ALTER TABLE faceit_records
         ADD COLUMN enemy_team_first_half_score integer,
         ADD COLUMN enemy_team_second_half_score integer,
         ADD COLUMN enemy_team_overtime_score integer
    """)
