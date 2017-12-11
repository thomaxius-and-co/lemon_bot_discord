async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE faceit_live_stats (
            faceit_guid TEXT NOT NULL REFERENCES faceit_guild_players_list(faceit_guid),
            faceit_elo TEXT NOT NULL,
            faceit_skill TEXT NOT NULL,
            faceit_ranking TEXT NOT NULL,
            removed TEXT NOT NULL DEFAULT FALSE,
            changed TIMESTAMP NOT NULL
        );
    """)
