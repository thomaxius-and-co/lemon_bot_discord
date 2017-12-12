import aiohttp
import asyncio
import util
import logger
import database as db
import discord
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


async def update_faceit_channel(channel):
    await db.execute("""
                  UPDATE faceit_guild_players_list
      SET spam_channel_id = $1""", channel)
    log.info('Updated faceit spam channel: %s' % channel)

async def get_channel_info(client, user_channel_name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == user_channel_name.lower():
            return channel.id
    return False #If channel doesn't exist

async def cmd_add_faceit_channel(client, message, arg):
    print(message.channel, type(message.channel))
    channel = await get_channel_info(client, arg)
    if not channel:
        await client.send_message(message.channel, 'No such channel.')
        return
    else:
        await update_faceit_channel(channel)
        await client.send_message(message.channel, 'Faceit spam channel added.')
        return



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
        msg = ''
        for row in guild_faceit_players_entries:
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

async def insert_data_to_player_stats_table(guid, elo, skill_level, ranking):
    await db.execute("""
        INSERT INTO faceit_live_stats AS a
        (faceit_guid, faceit_elo, faceit_skill, faceit_ranking, changed)
        VALUES ($1, $2, $3, $4, current_timestamp)""", str(guid), str(elo), str(skill_level), str(ranking))
    log.info('Added a player into stats database: faceit_guid: %s, elo %s, skill_level: %s, ranking: %s' % (
        guid, elo, skill_level, ranking))

async def check_faceit_stats(client):
    fetch_interval = 60
    while True:
        faceit_players = await get_guild_faceit_players()
        if not faceit_players:
            return
        log.info('Checking faceit stats')
        old_toplist = []
        new_toplist = []
        for record in faceit_players:
            player_stats = await get_faceit_stats_of_player(record['faceit_guid'])
            if player_stats:
                current_elo, skill_level, csgo_name, ranking = await get_user_stats_from_api(None, None, record['faceit_nickname'])
                if current_elo == '-':
                    continue
                item = record['faceit_nickname'], player_stats['faceit_ranking']

                old_toplist.append(item) #These are for later on, compare old list with new and see which player one passes..
                old_toplist = sorted(old_toplist, key=lambda x: x[1])
                item = record['faceit_nickname'], ranking
                new_toplist.append(item)

                if (str(current_elo) != str(player_stats['faceit_elo'])):
                    await insert_data_to_player_stats_table(record['faceit_guid'], current_elo, skill_level, ranking)
                    if record['spam_channel_id']:
                        await spam_about_elo_changes(client, record['faceit_nickname'], int(record['spam_channel_id']),
                                                     int(current_elo), int(player_stats['faceit_elo']), int(skill_level),
                                                     int(player_stats['faceit_skill']), (' "' + record['custom_nickname'] + '"' if record['custom_nickname'] else ''))
            else:
                current_elo, skill_level, csgo_name, ranking = await get_user_stats_from_api(None, None,
                                                                                             record['faceit_nickname'])
                if current_elo == '-':
                    continue
                await insert_data_to_player_stats_table(record['faceit_guid'], current_elo, skill_level, ranking)
        log.info('Faceit stats checked')
        await asyncio.sleep(fetch_interval)

async def set_faceit_nickname(faceit_name, custom_nickname):
    log.info("Setting nickname %s for: %s" % (faceit_name, custom_nickname))
    await db.execute("UPDATE faceit_guild_players_list SET custom_nickname = $1 where faceit_nickname = $2", custom_nickname, faceit_name)

async def cmd_add_faceit_nickname(client, message, arg):
    if not arg:
        await client.send_message(message.channel, "Usage: !addfaceitnickname <faceit user> <nickname>\n for example: !addfaceitnickname Thomaxius pussydestroyer")
        return
    faceit_name, custom_nickname = arg.split(' ',1)
    if not faceit_name or not custom_nickname:
        await client.send_message(message.channel, "Usage: !addfaceitnickname <faceit user> <nickname>\n for example: !addfaceitnickname Thomaxius The pussy destroyer")
        return
    players = await get_guild_faceit_players()
    for player in players:
        if player['faceit_nickname'] == faceit_name:
            await set_faceit_nickname(faceit_name, custom_nickname)
            await client.send_message(message.channel, "Nickname %s set for %s." % (custom_nickname, faceit_name))
            return
    await client.send_message(message.channel, "Player %s not found in database. " % faceit_name)



async def spam_about_elo_changes(client, faceit_nickname, spam_channel_id, current_elo, elo_before, current_skill, skill_before, custom_nickname):
    await asyncio.sleep(0.1)
    channel = discord.Object(id=spam_channel_id)
    if skill_before < current_skill:
        util.threadsafe(client, client.send_message(channel, '**%s%s** gained **%s** elo and a new skill level! (Skill level %s -> %s, Elo now: %s)' % (faceit_nickname, custom_nickname,  int(current_elo - elo_before), skill_before, current_skill,  current_elo)))
        return
    if skill_before > current_skill:
        util.threadsafe(client, client.send_message(channel, '**%s%s** lost **%s** elo and lost a skill level! (Skill level %s -> %s, Elo now: %s)' % (faceit_nickname, custom_nickname,  int(current_elo - elo_before), skill_before, current_skill, current_elo)))
        return
    if current_elo > elo_before:
        util.threadsafe(client, client.send_message(channel, '**%s%s** gained **%s** elo! (%s -> %s)' % (faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo)))
        return
    if elo_before > current_elo:
        util.threadsafe(client, client.send_message(channel, '**%s%s** lost **%s** elo! (%s -> %s)' % (faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo)))
        return



async def get_guild_faceit_players():
    return await db.fetch("""
        SELECT 
            *
        FROM
            faceit_guild_players_list
        """)

def register(client):
    util.start_task_thread(check_faceit_stats(client))
    return {
        'faceitstats': cmd_faceit_stats,
        'addfaceituser': cmd_add_faceit_user_into_database,
        'listfaceitusers': cmd_list_faceit_users,
        'deletefaceitusers': cmd_del_faceit_user,
        'addfaceitchannel': cmd_add_faceit_channel,
        'addfaceitnickname': cmd_add_faceit_nickname
    }
