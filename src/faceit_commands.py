import aiohttp
import asyncio
import util
import logger
import inspect
import database as db
import discord
import faceit_api
import columnmaker
from time_util import to_helsinki
from util import pmap

FACEIT_API_ERROR = False

log = logger.get("FACEIT")

async def cmd_faceit_stats(client, message, faceit_nickname, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname to search for.")
        return
    csgo_elo, skill_level, csgo_name, ranking_eu = await get_user_stats_from_api(client, message, faceit_nickname)
    if csgo_name:
        await client.send_message(message.channel, "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**EU ranking**: %s\n**CS:GO Elo**: %s\n**Skill level**: %s" % (faceit_nickname, csgo_name,  ranking_eu, csgo_elo, skill_level))
    else:
        return

async def cmd_faceit_commands(client, message, arg):
    errormessage = "Available faceit commands: " \
                   "```" \
                   "\n!faceit + " \
                   "\n<stats> <faceit nickname>" \
                   "\n<adduser> <faceit nickname>" \
                   "\n<listusers>" \
                   "\n<deluser> <faceit nickname or id (use !faceit listusers>" \
                   "\n<setchannel> <channel name where faceit spam will be spammed>" \
                   "\n<addnick <faceit actual nickname> <faceit custom nickname>" \
                   "\n<toplist>" \
                   "```"
    if not arg:
        await client.send_message(message.channel, errormessage)
        return
    if arg.lower() == 'listusers':
        await cmd_list_faceit_users(client, message, arg, obsolete=False)
        return
    elif arg.lower() == 'toplist':
        await cmd_do_faceit_toplist(client, message, arg)
    try:
        arg, secondarg = arg.split(' ',1)
    except ValueError:
        secondarg = None
    arg = arg.lower()
    if arg == 'stats':
        await cmd_faceit_stats(client, message, secondarg, obsolete=False)
    elif arg == 'adduser':
        await cmd_add_faceit_user_into_database(client, message, secondarg, obsolete=False)
    elif arg == 'deluser':
        await cmd_del_faceit_user(client, message, secondarg, obsolete=False)
    elif arg == 'setchannel':
        await cmd_add_faceit_channel(client, message, secondarg, obsolete=False)
    elif arg == 'addnick':
        await cmd_add_faceit_nickname(client, message, secondarg, obsolete=False)
    else:
        await client.send_message(message.channel, errormessage)
        return


async def get_user_stats_from_api(client, message, faceit_nickname):
    user, error = await faceit_api.user(faceit_nickname)
    if error:
        log.error(error)
        if client and message:
            await client.send_message(message.channel, error)
        return None, None, None, None
    csgo_name = user.get("csgo_name", None)
    skill_level = user.get("games", {}).get("csgo", {}).get("skill_level", None)
    csgo_elo = user.get("games", {}).get("csgo", {}).get("faceit_elo", None)
    ranking = await faceit_api.ranking(user.get("guid", {})) if csgo_elo else None
    return csgo_elo, skill_level, csgo_name, ranking

async def get_faceit_guid(client, message, faceit_nickname):
    user, error = await faceit_api.user(faceit_nickname)
    if error:
        await client.send_message(message.channel, error)
        return None
    return user.get("guid", None)

async def cmd_add_faceit_user_into_database(client, message, faceit_nickname, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    guild_id = message.server.id
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname for the user to be added, "
                                                   "for example: !faceit adduser Jallu-rce")
        return
    faceit_guid = await get_faceit_guid(client, message, faceit_nickname)
    if faceit_guid:
        await add_faceit_user_into_database(faceit_nickname, faceit_guid, message)
        if not await assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
            await client.send_message(message.channel, "%s is already in the database." % faceit_nickname)
        else:
            await client.send_message(message.channel, "Added %s into the database." % faceit_nickname)


async def assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
    already_in_db = await db.fetchval("SELECT count(*) = 1 FROM faceit_guild_ranking WHERE guild_id = $1 AND faceit_guid = $2", guild_id, faceit_guid)
    if already_in_db == True:
        return False

    await db.execute("INSERT INTO faceit_guild_ranking (guild_id, faceit_guid) VALUES ($1, $2)", guild_id, faceit_guid)
    return True

async def add_faceit_user_into_database(faceit_nickname, faceit_guid, message):
    await db.execute("INSERT INTO faceit_player (faceit_nickname, faceit_guid) VALUES ($1, $2) ON CONFLICT DO NOTHING", faceit_nickname, faceit_guid)

async def update_faceit_channel(guild_id, channel_id):
    await db.execute("""
        INSERT INTO faceit_notification_channel (guild_id, channel_id) VALUES ($1, $2)
        ON CONFLICT (guild_id) DO UPDATE SET channel_id = EXCLUDED.channel_id
    """, guild_id, channel_id)

async def get_user_stats_from_api_for_leaderboard(faceit_nickname):
    user, error = await faceit_api.user(faceit_nickname)
    if error:
        global FACEIT_API_ERROR
        FACEIT_API_ERROR = True
        return None, None
    skill_level = user.get("games", {}).get("csgo", {}).get("skill_level", 0)
    csgo_elo = user.get("games", {}).get("csgo", {}).get("faceit_elo", 0)
    return csgo_elo, skill_level

async def get_channel_id(client, user_channel_name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == user_channel_name.lower():
            return channel.id
    return False #If channel doesn't exist

async def cmd_add_faceit_channel(client, message, arg, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    if not arg:
        await client.send_message(message.channel, 'You must specify a channel name.')
        return
    guild_id = message.server.id
    channel_id = await get_channel_id(client, arg)
    if not channel_id:
        await client.send_message(message.channel, 'No such channel.')
        return
    else:
        await update_faceit_channel(guild_id, channel_id)
        await client.send_message(message.channel, 'Faceit spam channel added.')
        return

async def cmd_del_faceit_user(client, message, arg, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    guild_id = message.server.id
    if not arg:
        await client.send_message(message.channel, "You must specify faceit nickname, or an ID to delete, eq. !faceit deluser 1. "
                                                   "Use !faceit list to find out the correct ID.")
        return
    guild_faceit_players_entries = await get_all_faceit_players()
    if not guild_faceit_players_entries:
        await client.send_message(message.channel, "There are no faceit players added.")
        return
    if arg.isdigit():
        for entry in guild_faceit_players_entries:
            if int(arg) == entry['id']:
                await delete_faceit_user_from_database_with_row_id(guild_id, entry['id'])
                await client.send_message(message.channel, "User %s succesfully deleted." % entry['faceit_nickname'])
                return
        await client.send_message(message.channel, "No such ID in list. Use !faceit listusers.")
        return
    else:
        for entry in guild_faceit_players_entries:
            if arg == entry['faceit_nickname']:
                await delete_faceit_user_from_database_with_faceit_nickname(guild_id, entry['faceit_nickname'])
                await client.send_message(message.channel, "Faceit user %s succesfully deleted." % entry['faceit_nickname'])
                return
        await client.send_message(message.channel, "No such user in list. Use !faceit list to display a list of ID's.")
        return

async def cmd_list_faceit_users(client, message, _, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    guild_faceit_players_entries = await get_all_faceit_players()
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
            faceit_ranking,
            faceit_elo,
            faceit_skill
        FROM
            faceit_live_stats
        WHERE
            faceit_guid = $1
        ORDER BY
            changed DESC
        LIMIT
            1
        """, guid)

async def get_archieved_toplist_per_guild():
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
    log.info('Added a player into stats database: faceit_guid: %s, elo %s, skill_level: %s, ranking: %s', guid, elo, skill_level, ranking)

async def elo_notifier_task(client):
    fetch_interval = 60
    while True:
        await asyncio.sleep(fetch_interval)
        try:
            await check_faceit_elo(client)
        except Exception as e:
            log.error("Failed to check faceit stats: ")
            await util.log_exception(log)

async def check_faceit_elo(client):
    log.info('Faceit stats checking started')
    faceit_players = await get_all_faceit_players()
    if not faceit_players:
        return
    old_toplist_dict = await get_server_rankings_per_guild()
    for record in faceit_players:
        player_stats = await get_faceit_stats_of_player(record['faceit_guid'])
        if player_stats:
            current_elo, skill_level, csgo_name, ranking = await get_user_stats_from_api(client, None, record['faceit_nickname'])
            if not current_elo or not ranking or not player_stats['faceit_ranking'] or not player_stats['faceit_ranking']: # Currently, only EU ranking is supported
                continue
            if current_elo != player_stats['faceit_elo']:
                await insert_data_to_player_stats_table(record['faceit_guid'], current_elo, skill_level, ranking)
                for channel_id in await channels_to_notify_for_user(record["faceit_guid"]):
                    log.info("Notifying channel %s", channel_id)
                    await spam_about_elo_changes(client, record['faceit_nickname'], channel_id,
                                                 current_elo, player_stats['faceit_elo'], skill_level,
                                                 player_stats['faceit_skill'], (' "' + record['custom_nickname'] + '"' if record['custom_nickname'] else ''))
        else:
            current_elo, skill_level, csgo_name, ranking = await get_user_stats_from_api(client, None,
                                                                                         record['faceit_nickname'])
            if not current_elo or not ranking: # Currently, only EU ranking is supported
                continue
            await insert_data_to_player_stats_table(record['faceit_guid'], current_elo, skill_level, ranking)
    await compare_toplists(client, old_toplist_dict)
    log.info('Faceit stats checked')

async def compare_toplists(client, old_toplist_dict):
    new_toplist_dict = await get_server_rankings_per_guild()
    log.info("Comparing toplists")
    for key in old_toplist_dict:
        spam_channel_id = await get_spam_channel_by_guild(key)
        if not spam_channel_id: # Server doesn't like to be spammed, no need to do any work
            return
        old_toplist_sorted = sorted(old_toplist_dict.get(key), key=lambda x: x[2])[:11]
        new_toplist_sorted = sorted(new_toplist_dict.get(key), key=lambda x: x[2])[:11]
        log.info(old_toplist_sorted)
        log.info(new_toplist_sorted)
        if len(old_toplist_sorted) != len(new_toplist_sorted):
            log.info("Someone was added to faceit database, not making toplist comparision.")
            return
        elif old_toplist_sorted == new_toplist_sorted:
            log.info("No changes in rankings, not making comparsions")
            return
        else:
            await check_and_spam_rank_changes(client, old_toplist_sorted, new_toplist_sorted, spam_channel_id)

async def check_and_spam_rank_changes(client, old_toplist, new_toplist, spam_channel_id):
    log.info("Checking rank changes")
    msg = ""
    for item_at_oldlists_index, item_at_newlists_index in zip(old_toplist, new_toplist): #Compare each item of both lists side to side
        name_in_old_item = item_at_oldlists_index[0]  #Name of player in old toplist
        name_in_new_item = item_at_newlists_index[0] #Name of player in the same index in new toplist

        if name_in_old_item != name_in_new_item: # If the players don't match, it means player has dropped in the leaderboard
            player_new_rank_item = [item for item in new_toplist if
                                     item[0] == name_in_old_item and item[2] != item_at_oldlists_index[2]] # Find the player's item in the new toplist, but only if their ELO has changed aswell
            if player_new_rank_item: # If the player is found in new toplist
                old_rank = old_toplist.index(item_at_oldlists_index) + 1 # Player's old position (rank) in the old toplist
                new_rank = new_toplist.index(player_new_rank_item[0]) + 1 # Player's new position (rank) in the new toplist
                player_name = player_new_rank_item[0][0]
                if old_rank > new_rank:
                    print('msg', msg)
                    msg += "**%s** rose in server ranking! old rank **#%s**, new rank **#%s**\n" % (player_name, old_rank, new_rank)
                else:
                    msg += "**%s** fell in server ranking! old rank **#%s**, new rank **#%s**\n" % (player_name, old_rank, new_rank)
    if msg:
        log.info('Attempting to spam channel %s with the following message: %s' % (spam_channel_id, msg))
        channel = discord.Object(id=spam_channel_id)
        util.threadsafe(client, client.send_message(channel, msg))
    log.info("Rank changes checked")

async def channels_to_notify_for_user(guid):
    rows = await db.fetch("""
        SELECT channel_id
        FROM faceit_notification_channel
        JOIN faceit_guild_ranking USING (guild_id)
        WHERE faceit_guid = $1
    """, guid)
    return list(map(lambda r: r["channel_id"], rows))

async def get_spam_channel_by_guild(guild_id):
    result = await db.fetch("""
        SELECT channel_id
        FROM faceit_notification_channel
        WHERE guild_id = $1
    """, guild_id)
    return result[0]['channel_id']

async def set_faceit_nickname(guild_id, faceit_name, custom_nickname):
    log.info("Setting nickname %s for: %s", faceit_name, custom_nickname)
    await db.execute("""
        UPDATE faceit_guild_ranking gr SET custom_nickname = $1
        FROM faceit_player p WHERE p.faceit_guid = gr.faceit_guid
        AND gr.guild_id = $2 AND p.faceit_nickname = $3
    """, custom_nickname, guild_id, faceit_name)

async def cmd_add_faceit_nickname(client, message, arg, obsolete=True):
    if obsolete:
        await client.send_message(message.channel,
                                  '**This command is obsolete and will be replaced by:** !faceit ' + obsolete_commands_new_equivalents.get(
                                      inspect.stack()[0][3]))
    guild_id = message.server.id
    errormessage = "Usage: !faceit addnick <faceit user> <nickname>\n for example: !faceit addnick rce jallulover69"
    if not arg:
        await client.send_message(message.channel, errormessage)
        return
    try:
        faceit_name, custom_nickname = arg.split(' ',1)
    except ValueError:
        await client.send_message(message.channel, errormessage)
        return
    if not faceit_name or not custom_nickname:
        await client.send_message(message.channel, errormessage)
        return
    players = await get_all_faceit_players()
    for player in players:
        if player['faceit_nickname'] == faceit_name:
            await set_faceit_nickname(guild_id, faceit_name, custom_nickname)
            await client.send_message(message.channel, "Nickname %s set for %s." % (custom_nickname, faceit_name))
            return
    await client.send_message(message.channel, "Player %s not found in database. " % faceit_name)

async def spam_about_elo_changes(client, faceit_nickname, spam_channel_id, current_elo, elo_before, current_skill, skill_before, custom_nickname):
    await asyncio.sleep(0.1)
    channel = discord.Object(id=spam_channel_id)
    if skill_before < current_skill:
        util.threadsafe(client, client.send_message(channel, '**%s%s** gained **%s** elo and a new skill level! (Skill level %s -> %s, Elo now: %s)' % (faceit_nickname, custom_nickname,  int(current_elo - elo_before), skill_before, current_skill,  current_elo)))
        return
    elif skill_before > current_skill:
        util.threadsafe(client, client.send_message(channel, '**%s%s** lost **%s** elo and lost a skill level! (Skill level %s -> %s, Elo now: %s)' % (faceit_nickname, custom_nickname,  int(current_elo - elo_before), skill_before, current_skill, current_elo)))
        return
    elif current_elo > elo_before:
        util.threadsafe(client, client.send_message(channel, '**%s%s** gained **%s** elo! (%s -> %s)' % (faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo)))
        return
    elif elo_before > current_elo:
        util.threadsafe(client, client.send_message(channel, '**%s%s** lost **%s** elo! (%s -> %s)' % (faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo)))
        return

async def get_faceit_leaderboard(guild_id):
    faceit_users = await db.fetch("""
        SELECT faceit_nickname, faceit_guid
        FROM faceit_player
        JOIN faceit_guild_ranking USING (faceit_guid)
        WHERE guild_id = $1
    """, guild_id)

    if len(faceit_users) == 0:
        return None, None
    toplist = []

    batch_stats, batch_ranking = await asyncio.gather(
        pmap(get_user_stats_from_api_for_leaderboard, map(lambda u: u["faceit_nickname"], faceit_users)),
        pmap(faceit_api.ranking, map(lambda u: u["faceit_guid"], faceit_users)),
    )
    for i, user in enumerate(faceit_users):
        csgo_elo, skill_level = batch_stats[i]
        if (not csgo_elo and not skill_level) or not csgo_elo: #If the user is deleted from faceit database, or doesn't have elo
            continue
        eu_ranking = batch_ranking[i]
        if not eu_ranking:
            continue
        new_item = eu_ranking, user['faceit_nickname'], csgo_elo, skill_level
        toplist.append(new_item)

    global FACEIT_API_ERROR
    if FACEIT_API_ERROR:
        toplist = []
        FACEIT_API_ERROR = False
        ranking = await get_archieved_toplist(guild_id)
        for item in ranking:
            eu_ranking, faceit_nickname, csgo_elo, skill_level, last_entry_time = item
            if not eu_ranking:
                continue
            new_item = eu_ranking, faceit_nickname, csgo_elo, skill_level
            toplist.append(new_item)
        toplist_string = columnmaker.columnmaker(['EU RANKING', 'NAME', 'CS:GO ELO', 'SKILL LEVEL'], toplist)
        return toplist_string + ('\nShowing archieved stats as of %s as faceit live stats could not be fetched.' % to_helsinki(last_entry_time).strftime("%d/%m/%y %H:%M")), len(toplist)
    toplist = sorted(toplist, key=lambda x: x[0])[:10]
    return columnmaker.columnmaker(['EU RANKING', 'NAME', 'CS:GO ELO', 'SKILL LEVEL'], toplist), len(toplist)

async def get_server_rankings_per_guild():
    ranking = await get_archieved_toplist_per_guild()
    ranking_dict = {}
    for item in ranking:
        guild_id, nickname, elo, ranking = item
        if guild_id not in ranking_dict:
            ranking_dict.update({guild_id:[[nickname, elo, ranking]]})
        else:
            dict_item = ranking_dict.get(guild_id)
            dict_item.append([nickname, elo, ranking])
    return ranking_dict

async def get_archieved_toplist(guild_id):
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
              last_entry_time
            from 
              last_changed
            LEFT JOIN 
              ranking using (guild_id)     
            order by 
              faceit_ranking asc
            limit 10
            """, guild_id)

async def cmd_do_faceit_toplist(client, message, input):
    guild_id = message.server.id
    toplist, amountofpeople = await get_faceit_leaderboard(guild_id)
    if not toplist or not amountofpeople:
        await client.send_message(message.channel,
                                  'No faceit players have been added to the database, or none of them have rank.')
        return
    title = 'Top %s ranked faceit CS:GO players:' % (amountofpeople)
    await client.send_message(message.channel,
                              ('```%s \n' % title + toplist + '```'))
    return

async def get_all_faceit_players():
    return await db.fetch("SELECT * FROM faceit_guild_ranking JOIN faceit_player USING (faceit_guid) ORDER BY id ASC")

obsolete_commands_new_equivalents = {
    'cmd_add_faceit_user_into_database': 'adduser',
    'cmd_list_faceit_users': 'list',
    'cmd_del_faceit_user': 'deluser',
    'cmd_add_faceit_channel': 'addchannel',
    'cmd_add_faceit_nickname': 'addnick',
    'cmd_faceit_stats': 'stats'
}

def register(client):
    util.start_task_thread(elo_notifier_task(client))
    return {
        'faceit': cmd_faceit_commands,
        'faceitstats': cmd_faceit_stats,
        'addfaceituser': cmd_add_faceit_user_into_database,
        'listfaceitusers': cmd_list_faceit_users,
        'deletefaceitusers': cmd_del_faceit_user,
        'addfaceitchannel': cmd_add_faceit_channel,
        'addfaceitnickname': cmd_add_faceit_nickname
    }