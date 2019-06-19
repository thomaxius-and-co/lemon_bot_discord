async def exec(log, tx):
   await tx.execute("""
        CREATE TABLE IF NOT EXISTS faceit_records (
            id serial,
            match_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            faceit_guid TEXT REFERENCES faceit_player (faceit_guid) NOT NULL,
            win boolean,
            player_team_rank integer,
            player_team_first_half_score integer,
            player_team_second_half_score integer,
            player_team_overtime_score integer,
            started_at integer,
            finished_at integer,         
            added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            kills integer,
            assists integer,
            deaths integer,
            headshots integer,
            headshot_percentage numeric,
            mvps integer,            
            triple_kills integer,
            quadro_kills integer,
            penta_kills integer,
            kd_ratio numeric(10,2),
            kr_ratio numeric(10,2),
            dpr_ratio numeric(10,2),
            total_rounds integer, 
            match_length_seconds integer
            );
    """)
