async def exec(log, tx):
    await tx.execute("""
        CREATE TABlE faceit_aliases (
            faceit_guid TEXT NOT NULL REFERENCES faceit_player (faceit_guid),
            faceit_nickname TEXT NOT NULL, 
            created timestamp without time zone DEFAULT current_timestamp NOT NULL
        );
    """)
