async def exec(log, tx):
    # Make faceit_ranking nullable because it contains 'None' as ranking
    await tx.execute("ALTER TABLE faceit_live_stats ALTER COLUMN faceit_ranking DROP NOT NULL")
    # Fix 'None' rankings to NULL
    await tx.execute("UPDATE faceit_live_stats SET faceit_ranking = NULL WHERE faceit_ranking = 'None'")

    # Fix numeric column types
    for column in ["faceit_elo", "faceit_ranking", "faceit_skill"]:
        await tx.execute("ALTER TABLE faceit_live_stats ALTER COLUMN " + column + " TYPE BIGINT USING " + column + "::BIGINT")

    # Fix removed column to bool
    await tx.execute("ALTER TABLE faceit_live_stats ALTER COLUMN removed TYPE BOOL USING removed::BOOL")
