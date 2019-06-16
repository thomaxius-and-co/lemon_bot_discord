import logger
import database as db



log = logger.get("FACEIT_DB")

async def update_nickname(faceit_guid, api_player_name):
    async with db.transaction() as tx:
        await tx.execute("INSERT INTO faceit_aliases (faceit_guid, faceit_nickname) VALUES ($1, $2)", faceit_guid,
                         api_player_name)
        await tx.execute("UPDATE faceit_player SET faceit_nickname = $1 WHERE faceit_guid = $2", api_player_name,
                         faceit_guid)
    log.info("Updated nickname %s for user %s" % (api_player_name, faceit_guid))


async def add_nickname(faceit_guid, api_player_name):
    async with db.transaction() as tx:
        await tx.execute("INSERT INTO faceit_aliases (faceit_guid, faceit_nickname) VALUES ($1, $2)", faceit_guid,
                         api_player_name)
    log.info("Added new nickname %s for user %s" % (api_player_name, faceit_guid))


async def channels_to_notify_for_user(guid):
    rows = await db.fetch("""
        SELECT channel_id, custom_nickname
        FROM faceit_notification_channel
        JOIN faceit_guild_ranking USING (guild_id)
        WHERE faceit_guid = $1
    """, guid)
    return map(lambda r: (r["channel_id"], r["custom_nickname"]), rows)


async def get_spam_channel_by_guild(guild_id):
    return await db.fetchval("""
        SELECT channel_id
        FROM faceit_notification_channel
        WHERE guild_id = $1
    """, guild_id)


async def set_faceit_nickname(guild_id, faceit_name, custom_nickname):
    log.info("Setting nickname %s for: %s", faceit_name, custom_nickname)
    await db.execute("""
        UPDATE faceit_guild_ranking gr SET custom_nickname = $1
        FROM faceit_player p WHERE p.faceit_guid = gr.faceit_guid
        AND gr.guild_id = $2 AND p.faceit_nickname = $3
    """, custom_nickname, guild_id, faceit_name)


async def get_toplist_from_db(guild_id):
    return await db.fetch("""
            with ranking as 
            (
              select distinct ON 
                (faceit_guid) faceit_guid, 
                 faceit_ranking, 
                 faceit_nickname, 
                 faceit_elo, 
                 faceit_skill,
                 guild_id,
                 changed
              from 
                  faceit_live_stats  
              join 
                  faceit_player using (faceit_guid) 
              join 
                  faceit_guild_ranking using (faceit_guid) 
              where 
                  guild_id = $1  and faceit_ranking > 0
              order by faceit_guid, changed desc
              ),
            last_changed as 
            (
            select
              max(changed) as last_entry_time,
              guild_id
            from
              faceit_live_stats
            join 
              faceit_guild_ranking using (faceit_guid) 
            where 
              guild_id = $1
            group BY 
              guild_id              
            )
            select 
              faceit_ranking, 
              faceit_nickname, 
              faceit_elo, 
              faceit_skill,
              last_entry_time,
              changed
            from 
              last_changed
            LEFT JOIN 
              ranking using (guild_id)     
            order by 
              faceit_ranking asc
            limit 10
            """, guild_id)


async def get_all_players():
    return await db.fetch("""
        SELECT faceit_guid, faceit_nickname FROM faceit_player
        WHERE faceit_guid IN (SELECT DISTINCT faceit_guid FROM faceit_guild_ranking)
        ORDER BY id ASC
    """)


async def get_players_in_guild(guild_id):
    return await db.fetch(
        "SELECT * FROM faceit_guild_ranking JOIN faceit_player USING (faceit_guid) WHERE guild_id = $1 ORDER BY id ASC",
        guild_id)


async def delete_faceit_user_from_database_with_row_id(guild_id, row_id):
    await db.execute("""
        DELETE FROM faceit_guild_ranking
        WHERE guild_id = $1 AND faceit_guid = (
            SELECT faceit_guid FROM faceit_player WHERE id = $2
        )
    """, guild_id, row_id)


async def delete_faceit_user_from_database_with_faceit_nickname(guild_id, faceit_nickname):
    await db.execute("""
        DELETE FROM faceit_guild_ranking
        WHERE guild_id = $1 AND faceit_guid = (
            SELECT faceit_guid FROM faceit_player WHERE faceit_nickname LIKE $2
        )
    """, guild_id, faceit_nickname)


async def get_faceit_stats_of_player(guid):
    return await db.fetchrow("""
        SELECT
            *
        FROM
            faceit_live_stats
        WHERE
            faceit_guid = $1
        ORDER BY
            changed DESC
        LIMIT
            1
        """, guid)


async def get_player_current_database_nickname(guid):
    return await db.fetchval("""
        SELECT
            faceit_nickname
        FROM
            faceit_player
        WHERE
            faceit_guid = $1
        LIMIT
            1
        """, guid)


async def get_toplist_per_guild_from_db():
    return await db.fetch("""
            with 
                latest_elo as 
                  (
                  select distinct on 
                      (faceit_guid) *
                  from 
                      faceit_live_stats
                  order by 
                      faceit_guid, changed desc
                  )
            select 
                guild_id, 
                faceit_nickname, 
                faceit_elo,
                faceit_ranking
            from 
                faceit_guild_ranking
            join 
                faceit_player using (faceit_guid)
            join 
                latest_elo using (faceit_guid)
            WHERE
                faceit_ranking > 0
            order by 
                guild_id, faceit_elo desc
            """)


async def insert_data_to_player_stats_table(guid, elo, skill_level, ranking):
    await db.execute("""
        INSERT INTO faceit_live_stats AS a
        (faceit_guid, faceit_elo, faceit_skill, faceit_ranking, changed)
        VALUES ($1, $2, $3, $4, current_timestamp)""", str(guid), elo, skill_level, ranking)
    log.info('Added a player into stats database: faceit_guid: %s, elo %s, skill_level: %s, ranking: %s', guid, elo,
             skill_level, ranking)



async def assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
    already_in_db = await db.fetchval(
        "SELECT count(*) = 1 FROM faceit_guild_ranking WHERE guild_id = $1 AND faceit_guid = $2", guild_id, faceit_guid)
    if already_in_db == True:
        return False

    await db.execute("INSERT INTO faceit_guild_ranking (guild_id, faceit_guid) VALUES ($1, $2)", guild_id, faceit_guid)
    return True


async def add_faceit_user_into_database(faceit_nickname, faceit_guid):
    await db.execute("INSERT INTO faceit_player (faceit_nickname, faceit_guid) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                     faceit_nickname, faceit_guid)


async def update_faceit_channel(guild_id, channel_id):
    await db.execute("""
        INSERT INTO faceit_notification_channel (guild_id, channel_id) VALUES ($1, $2)
        ON CONFLICT (guild_id) DO UPDATE SET channel_id = EXCLUDED.channel_id
    """, guild_id, channel_id)


async def get_player_add_date(faceit_guid):
    query_result = await db.fetchval("""        
        SELECT
            min(changed)
        FROM
            faceit_live_stats
        WHERE
            faceit_guid = $1
            """, faceit_guid)
    return query_result.date()


async def get_player_aliases(faceit_guid):
    return await db.fetch("""        
        SELECT
            faceit_nickname, created
        FROM
            faceit_aliases
        WHERE
            faceit_guid = $1 AND faceit_nickname not in (SELECT faceit_nickname FROM faceit_player)
        ORDER BY
            created DESC""", faceit_guid)