import aiohttp
import asyncio
import logger
import database as db
import faceit_api
log = logger.get("FACEIT")

async def cmd_faceit_stats(client, message, faceit_nickname):
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname to search for.")
        return
    csgo_elo, skill_level, csgo_name, ranking_eu = await get_user_stats_from_api(client, message, faceit_nickname)
    if csgo_name:
        await client.send_message(message.channel, "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**EU ranking**: %s\n**CS:GO Elo**: %s\n**Skill level**: %s" % (faceit_nickname, csgo_name,  ranking_eu, csgo_elo, skill_level))
    else:
        return

async def get_user_stats_from_api(client, message, faceit_nickname):
    user, error = await faceit_api.user(faceit_nickname)
    if error:
        await client.send_message(message.channel, error)
        return None, None, None, None
    csgo_name = user.get("csgo_name", "-")
    skill_level = user.get("games", {}).get("csgo", {}).get("skill_level", "-")
    csgo_elo = user.get("games", {}).get("csgo", {}).get("faceit_elo", "-")
    ranking = await faceit_api.ranking(user.get("guid", {})) if csgo_elo != "-" else "-"
    return str(csgo_elo), str(skill_level), csgo_name, ranking

async def get_faceit_guid(client, message, faceit_nickname):
    user, error = await faceit_api.user(faceit_nickname)
    if error:
        await client.send_message(message.channel, error)
        return None
    return user.get("guid", None)

async def cmd_add_faceit_user_into_database(client, message, faceit_nickname):
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname for it to be added.")
        return
    faceit_guid = await get_faceit_guid(client, message, faceit_nickname)
    if faceit_guid:
        await add_faceit_user_into_database(faceit_nickname, faceit_guid, message)
        await client.send_message(message.channel, "Added %s into the database" % faceit_nickname)

async def add_faceit_user_into_database(faceit_nickname, faceit_guid, message):
        await db.execute("""
            INSERT INTO faceit_guild_players_list AS a
            (faceit_nickname, faceit_guid, message_id)
            VALUES ($1, $2, $3)""", faceit_nickname, faceit_guid, message.id)
        log.info('Added a player into database: %s, faceit_guid: %s, message_id %s, added by: %s' % (
            faceit_nickname, faceit_guid, message.author.id, message.author))



async def cmd_del_faceit_user(client, message, arg):
    if not arg:
        await client.send_message(message.channel, "You must specify faceit nickname, or an ID to delete, eq. !delfaceituser 1. "
                                                   "Use !listfaceitusers to find out the correct ID.")
        return
    guild_faceit_players_entries = await get_guild_faceit_players()
    if not guild_faceit_players_entries:
        await client.send_message(message.channel, "There are no faceit players added.")
        return
    if arg.isdigit():
        for entry in guild_faceit_players_entries:
            if int(arg) == entry['id']:
                await delete_faceit_user_from_database_with_row_id(entry['id'])
                await client.send_message(message.channel, "User %s succesfully deleted." % entry['faceit_nickname'])
                return
        await client.send_message(message.channel, "No such ID in list. Use !listfaceitusers.")
        return
    else:
        for entry in guild_faceit_players_entries:
            if arg == entry['faceit_nickname']:
                await delete_faceit_user_from_database_with_faceit_nickname(entry['faceit_nickname'])
                await client.send_message(message.channel, "Faceit user %s succesfully deleted." % entry['faceit_nickname'])
                return
        await client.send_message(message.channel, "No such user in list. Use !listfaceitusers to display a list of ID's.")
        return

async def cmd_list_faceit_users(client, message, _):
    guild_faceit_players_entries = await get_guild_faceit_players()
    if not guild_faceit_players_entries:
        await client.send_message(message.channel, "No faceit users have been defined.")
        return
    else:
        for row in guild_faceit_players_entries:
            msg = ''
            faceit_player = row['faceit_nickname']
            faceit_id = row['id']
            msg += str(faceit_id) + '. ' + faceit_player + '\n'
            await client.send_message(message.channel, msg)

async def delete_faceit_user_from_database_with_row_id(row_id):
    log.info("DELETE from faceit_guild_players_list where id like %s" % row_id)
    await db.execute("DELETE from faceit_guild_players_list where id = $1", row_id)

async def delete_faceit_user_from_database_with_faceit_nickname(faceit_nickname):
    log.info("DELETE from faceit_guild_players_list where faceit_nickname like %s" % faceit_nickname)
    await db.execute("DELETE from faceit_guild_players_list where faceit_nickname like $1", faceit_nickname)

async def get_guild_faceit_players():
    return await db.fetch("""
        SELECT 
            *
        FROM
            faceit_guild_players_list
        """)

def register(client):
    return {
        'faceitstats': cmd_faceit_stats,
        'addfaceituser': cmd_add_faceit_user_into_database,
        'listfaceitusers': cmd_list_faceit_users,
        'deletefaceitusers': cmd_del_faceit_user
    }
