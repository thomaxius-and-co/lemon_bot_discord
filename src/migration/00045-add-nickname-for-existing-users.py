async def exec(log, tx):
    await tx.execute("""
        INSERT INTO 
                faceit_aliases (faceit_guid, faceit_nickname)

        SELECT 
                faceit_guid, faceit_nickname 
        FROM 
                faceit_player p
        WHERE NOT EXISTS 
                (
                  SELECT 
                        * 
                  FROM 
                        faceit_aliases a 
                  WHERE 
                        a.faceit_guid = p.faceit_guid
                )            
                            """)