import aiohttp
import asyncio
import logger
import database as db
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
    user_stats_url = "https://api.faceit.com/api/nicknames/" + faceit_nickname
    async with aiohttp.ClientSession() as session:
        response = await session.get(user_stats_url)
        log.info("GET %s %s %s", response.url, response.status, await response.text())
        result = await response.json()
        if result['result'] == 'error':
            await client.send_message(message.channel, result['message'].title() + ".") #Yes, I am this triggered by the first letter being a non-capital
            return None, None, None, None
        csgo_name = result.get("payload", {}).get("csgo_name", "-")
        skill_level = result.get("payload", {}).get("games", {}).get("csgo", {}).get("skill_level", "-")
        csgo_elo = result.get("payload", {}).get("games", {}).get("csgo", {}).get("faceit_elo", "-")
        ranking = await get_user_eu_ranking(result.get("payload", {}).get("guid", {})) if csgo_elo != "-" else "-"
        return str(csgo_elo), str(skill_level), csgo_name, ranking

async def get_faceit_guid(client, message, faceit_nickname):
    user_stats_url = "https://api.faceit.com/api/nicknames/" + faceit_nickname
    async with aiohttp.ClientSession() as session:
        response = await session.get(user_stats_url)
        log.info("GET %s %s %s", response.url, response.status, await response.text())
        result = await response.json()
        if result['result'] == 'error':
            await client.send_message(message.channel, result['message'].title() + ".") #Yes, I am this triggered by the first letter being a non-capital
            return None
        return result.get("payload", {}).get("guid", None)

async def get_user_eu_ranking(faceit_guid):
    eu_ranking_url = "https://api.faceit.com/ranking/v1/globalranking/csgo/EU/" + faceit_guid
    async with aiohttp.ClientSession() as session:
        response = await session.get(eu_ranking_url)
        log.info("GET %s %s %s", response.url, response.status, await response.text())
        result = await response.json()
        return str(result.get("payload", "-"))

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
    if arg.isdigit() and (int(arg) <= len(guild_faceit_players_entries)): #There is a slight problem with this.. if the faceit nickname is entire numeric, it will think that the user is trying to type an ID and not the name..
        index = int(arg) - 1
        if index > len(guild_faceit_players_entries) - 1 or int(
                arg) == 0:  # While defining 0 as an ID works, we don't want that heh
            await client.send_message(message.channel, "No such ID in list.")
            return
        await delete_faceit_user_from_database_with_message_id(guild_faceit_players_entries[index]['message_id'])
        await client.send_message(message.channel, "Faceit user succesfully deleted.")
        return
    else:
        for entry in guild_faceit_players_entries:
            if arg == entry['faceit_nickname']:
                await delete_faceit_user_from_database_with_faceit_nickname(entry['faceit_nickname'])
                await client.send_message(message.channel, "Faceit user succesfully deleted.")
                return
        await client.send_message(message.channel, "No such user in list. Use !listfaceitusers to display a list of ID's.")
        return

async def cmd_list_faceit_users(client, message, _):
    guild_faceit_players_entries = await get_guild_faceit_players()
    if not guild_faceit_players_entries:
        await client.send_message(message.channel, "No faceit users have been defined.")
        return
    else:
        msg = ''
        i = 1
        for row in guild_faceit_players_entries:
            faceit_players = row['faceit_nickname']
            ID = str(i) + ': '
            msg += ID + faceit_players + '\n'
            i += 1
        await client.send_message(message.channel, msg)

async def delete_faceit_user_from_database_with_message_id(message_id):
    log.info("DELETE from faceit_guild_players_list where message_id like %s" % message_id)
    await db.execute("DELETE from faceit_guild_players_list where message_id like $1", message_id)

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
