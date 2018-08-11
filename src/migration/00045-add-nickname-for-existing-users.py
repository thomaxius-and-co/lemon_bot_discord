async def exec(log, tx):
    async def all_players_have_nickname():
        return (await tx.fetchval("""
                                      select
                                            count(*) 
                                      from 
                                            faceit_player
                                            """)) ==  \
               (await tx.fetchval("""
                                      select 
                                            count(*) 
                                      from 
                                          (select distinct on (faceit_guid) faceit_guid 
                                                  from faceit_aliases) as subquery
                                                """)) # This checks if amount of players with a nickname is the same as amount of players in the players table.

    amount_of_players = await tx.fetchval("""
                                          select 
                                                count(*) 
                                          from 
                                                faceit_player
                                            """)
    if not await all_players_have_nickname():
        for x in range(amount_of_players-1):
            log.info("Adding player %s" % x)
            await tx.execute("""
                INSERT INTO 
                    faceit_aliases (faceit_guid, faceit_nickname) 
                VALUES 
                    (
                        (SELECT 
                            faceit_guid 
                        FROM 
                            faceit_player 
                        WHERE 
                            faceit_guid NOT IN (
                                                SELECT 
                                                      faceit_guid 
                                                FROM 
                                                      faceit_aliases)
                                                ORDER BY
                                                      faceit_guid DESC
                                                LIMIT 1), 
                        (SELECT 
                            faceit_nickname 
                        FROM 
                            faceit_player 
                        WHERE 
                            faceit_guid NOT IN (
                                                SELECT 
                                                      faceit_guid 
                                                FROM 
                                                      faceit_aliases)
                        ORDER BY
                              faceit_guid DESC
                        LIMIT 1
                        ))                  
                 ON CONFLICT DO NOTHING
            """)
    else:
        log.info("All players in database have a nickname inserted into aliases table, no need to run this migration.")