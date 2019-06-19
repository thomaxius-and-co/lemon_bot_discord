async def exec(log, tx):

    await tx.execute("""
        CREATE TABLE IF NOT EXISTS faceit_records (
            id serial,
            player_guid TEXT NOT NULL REFERENCES discord_user (user_id),
            player_guild TEXT NOT NULL,
            match_id TEXT NOT NULL,
            kills integer NOT NULL,
            assists integer NOT NULL,
            deaths integer NOT NULL,
            headshots integer NOT NULL,
            headshot_percentage decimal NOT NULL,
            mvps integer NOT NULL,            
            triple_kills integer NOT NULL,
            quadro_kills integer NOT NULL,
            penta_kills integer NOT NULL,
            kd_ratio integer NOT NULL,
            kr_ratio integer NOT NULL,
            win boolean NOT NULL,
            rounds integer NOT NULL, 
            player_team_rank integer NOT NULL,
            player_team_first_half_score integer NOT NULL,
            player_team_second_half_score integer NOT NULL,
            player_team_overtime_score integer NOT NULL,
            match_started_at integer NOT NULL,
            match_finished_at integer NOT NULL,            
            match_total_rounds integer NOT NULL,          
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            record_identifier TEXT NOT NULL,
            );
    """)
