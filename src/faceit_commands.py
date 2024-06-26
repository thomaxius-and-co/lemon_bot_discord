import logger
from discord.abc import GuildChannel
import faceit_db_functions as faceit_db
import faceit_api
from faceit_api import NotFound, UnknownError
from tablemaker import tablemaker
from time_util import as_helsinki, to_utc
from datetime import datetime
import faceit_common as fc
import faceit_records as fr
import asyncio
log = logger.get("FACEIT_COMMANDS")


async def cmd_do_faceit_toplist(client, message, input):
    if not isinstance(message.channel, GuildChannel):
        await message.channel.send('This command does not work on private servers.')
        return
    toplist, amountofpeople = await get_faceit_leaderboard(message.guild.id)
    if not toplist or not amountofpeople:
        await message.channel.send('No faceit players have been added to the database, or none of them have rank.')
        return
    title = 'Top %s ranked faceit CS:GO players:' % (amountofpeople)
    await message.channel.send(('```%s \n' % title + toplist + '```'))


async def cmd_add_faceit_nickname(client, message, arg):
    guild_id = message.guild.id
    errormessage = "Usage: !faceit addnick <faceit user> <nickname>\n for example: !faceit addnick rce jallulover69"
    if not arg:
        await message.channel.send(errormessage)
        return
    try:
        faceit_name, custom_nickname = arg.split(' ', 1)
    except ValueError:
        await message.channel.send(errormessage)
        return
    if not faceit_name or not custom_nickname:
        await message.channel.send(errormessage)
        return
    for player in await faceit_db.get_players_in_guild(guild_id):
        if player['faceit_nickname'] == faceit_name:
            await faceit_db.set_faceit_nickname(guild_id, faceit_name, custom_nickname)
            await message.channel.send("Nickname %s set for %s." % (custom_nickname, faceit_name))
            return
    await message.channel.send("Player %s not found in database. " % faceit_name)


async def cmd_faceit_stats(client, message, faceit_nickname):
    if not faceit_nickname:
        await message.channel.send("You need to specify a faceit nickname to search for.")
        return
    csgo_elo, skill_level, csgo_name, ranking_eu, last_played, faceit_url = await get_user_stats_from_api_by_nickname(
        client, message, faceit_nickname)
    log.info("%s, %s, %s, %s, %s, %s)" % (csgo_elo, skill_level, csgo_name, ranking_eu, last_played, faceit_url))
    aliases_string = "\n**Previous nicknames**: %s" % await get_player_aliases_string(
        await get_faceit_guid(faceit_nickname), faceit_nickname)
    if csgo_name:
        msg = "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**EU ranking**: %s\n**CS:GO Elo**: %s\n**Skill level**: %s\n**Last played**: %s%s\n**Faceit url**: %s" % (
            faceit_nickname, csgo_name, ranking_eu, csgo_elo, skill_level,
            to_utc(as_helsinki(datetime.fromtimestamp(last_played))).strftime("%d/%m/%y %H:%M") if last_played else '-',
            aliases_string, faceit_url)
        await message.channel.send(msg[:2000])


async def cmd_list_faceit_users(client, message, _):
    guild_faceit_players_entries = await faceit_db.get_players_in_guild(message.guild.id)
    if not guild_faceit_players_entries:
        await message.channel.send("No faceit users have been defined.")
        return
    else:
        msg = ''
        for row in guild_faceit_players_entries:
            faceit_player = row['faceit_nickname']
            faceit_id = row['id']
            msg += str(faceit_id) + '. ' + faceit_player + '\n'
        await message.channel.send(msg)


async def cmd_add_faceit_user_into_database(client, message, faceit_nickname):
    guild_id = message.guild.id
    if not faceit_nickname:
        await message.channel.send("You need to specify a faceit nickname for the user to be added, "
                                                   "for example: !faceit adduser Jallu-rce")
        return
    try:
        faceit_guid = await get_faceit_guid(faceit_nickname)
        await faceit_db.add_faceit_user_into_database(faceit_nickname, faceit_guid)
        if not await faceit_db.assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
            await message.channel.send("%s is already in the database." % faceit_nickname)
        else:
            await message.channel.send("Added %s into the database." % faceit_nickname)
            log.info("Adding stats for added player %s, guid %s" % (faceit_nickname, faceit_guid))
            current_elo, skill_level, csgo_name, ranking, last_played = await fc.get_user_stats_from_api_by_id(faceit_guid)
            if not current_elo or not ranking:  # Currently, only EU ranking is supported
                return
            if not (await faceit_db.get_player_aliases(faceit_guid)):
                await faceit_db.add_nickname(faceit_guid, csgo_name)
            else:
                log.info("Not adding a nickname for user since he already has one")
                await(fc.do_nick_change_check(faceit_guid, csgo_name,
                                           await faceit_db.get_player_current_database_nickname(faceit_guid)))
            await faceit_db.insert_data_to_player_stats_table(faceit_guid, current_elo, skill_level, ranking)

    except NotFound as e:
        await message.channel.send(str(e))
    except UnknownError as e:
        await message.channel.send("Unknown error")


async def cmd_del_faceit_user(client, message, arg):
    guild_id = message.guild.id
    if not arg:
        await message.channel.send("You must specify faceit nickname, or an ID to delete, eq. !faceit deluser 1. "
                                  "Use !faceit list to find out the correct ID.")
        return
    guild_faceit_players_entries = await faceit_db.get_players_in_guild(message.guild.id)
    if not guild_faceit_players_entries:
        await message.channel.send("There are no faceit players added.")
        return
    if arg.isdigit():
        for entry in guild_faceit_players_entries:
            if int(arg) == entry['id']:
                await faceit_db.delete_faceit_user_from_database_with_row_id(guild_id, entry['id'])
                await message.channel.send("User %s succesfully deleted." % entry['faceit_nickname'])
                return
        await message.channel.send("No such ID in list. Use !faceit listusers.")
        return
    else:
        for entry in guild_faceit_players_entries:
            if arg == entry['faceit_nickname']:
                await faceit_db.delete_faceit_user_from_database_with_faceit_nickname(guild_id, entry['faceit_nickname'])
                await message.channel.send("Faceit user %s succesfully deleted." % entry['faceit_nickname'])
                return
        await message.channel.send("No such user in list. Use !faceit listusers to display a list of ID's.")
        return


async def cmd_faceit_commands(client, message, arg):
    infomessage = "Available faceit commands: " \
                  "```" \
                  "\n!faceit + " \
                  "\n<stats> <faceit nickname>" \
                  "\n<adduser> <faceit nickname>" \
                  "\n<listusers>" \
                  "\n<deluser> <faceit nickname or id (use !faceit listusers>" \
                  "\n<setchannel> <channel name where faceit spam will be spammed>" \
                  "\n<addnick <faceit actual nickname> <faceit custom nickname>" \
                  "\n<toplist>" \
                  "\n<aliases>" \
                  "\n<records>" \
                  "```"
    if not isinstance(message.channel, GuildChannel):
        await private_faceit_commands(client, message, arg)
        return
    if not arg:
        await message.channel.send(infomessage)
        return
    if arg.lower() == 'listusers':
        await cmd_list_faceit_users(client, message, arg)
        return
    elif arg.lower() == 'toplist':
        await cmd_do_faceit_toplist(client, message, arg)
        return
    try:
        arg, secondarg = arg.split(' ', 1)
    except ValueError:
        secondarg = None
    arg = arg.lower()
    if arg == 'stats':
        await cmd_faceit_stats(client, message, secondarg)
        return
    elif arg == 'adduser':
        await cmd_add_faceit_user_into_database(client, message, secondarg)
        return
    elif arg == 'deluser':
        await cmd_del_faceit_user(client, message, secondarg)
        return
    elif arg == 'setchannel':
        await cmd_add_faceit_channel(client, message, secondarg)
        return
    elif arg == 'addnick':
        await cmd_add_faceit_nickname(client, message, secondarg)
        return
    elif arg == 'aliases':
        await cmd_show_aliases(client, message, secondarg)
        return
    elif arg == 'records':
        await cmd_show_records(client, message, secondarg)
        return
    elif arg == 'parsepastrecords':
        await cmd_parse_records_of_past_matches(client, message, secondarg)
        return
    elif arg == 'resetrecords':
        await cmd_reset_records(client, message, secondarg)
        return
    else:
        await message.channel.send(infomessage)
        return


async def cmd_reset_records(client, message, _):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await message.channel.send("You're not allowed to use this command.")
        return
    await message.channel.send("This will reset the records of this guild. Type 'yes' to confirm, "
                                               "or 'no' to cancel.")
    try:
        answer = await client.wait_for("message", timeout=60, check=lambda m: m.author == message.author)
        if answer.content.lower() == 'yes':
            await faceit_db.add_records_reset_date(message.guild.id, datetime.now(), message.author.id)
            log.info("User %s triggered rest of records for guild %s" % (message.author.id, message.guild.id))
            await message.channel.send("Records reset.")
        elif answer.content.lower() == 'no':
            await message.channel.send("Deletion of records cancelled.")
    except asyncio.TimeoutError:
        await message.channel.send("Deletion of records cancelled.")

    return


async def cmd_show_aliases(client, message, faceit_nickname):
    guild_players = await faceit_db.get_players_in_guild(message.guild.id)
    for record in guild_players:
        if faceit_nickname == record['faceit_nickname']:
            player_guid = await get_faceit_guid(faceit_nickname)
            if player_guid:
                aliases_query_result = await faceit_db.get_player_aliases(player_guid)
                if aliases_query_result:  # This is a bit lazy
                    alias_string = await get_player_aliases_string(player_guid, faceit_nickname)
                    msg = "**%s** has the following aliases: %s" % (faceit_nickname, alias_string)
                    await message.channel.send(msg[:2000])  # todo: replace this with some sort of 'long message splitter'
                    return
                else:
                    await message.channel.send("**%s** has no aliases." % (faceit_nickname))
                    return
    await message.channel.send("No such player in the server, use !faceit listusers.")


def widest_in_list_of_tuples(list_of_tuples, index):
    return len(max(list_of_tuples,key=lambda x: len(str(x[index])))[index])


async def cmd_show_records(client, message, _) -> None:
    guild_records = await fr.get_records_by_guild(message.guild.id)
    records_as_tuples = []
    for record in guild_records.values():
        record_item = record.get("record_item")
        record_title = record.get("record_title")
        record_minimum_requirement = record.get("minimum_requirement")
        record_function = record.get("function")
        if record_item:
            record_value = record_item[0][0]
            if record_function:
                record_value = await record_function(record_item)
            record_holder = record_item[0]['faceit_nickname']
            record_date = datetime.utcfromtimestamp(record_item[0]['finished_at']).strftime('%Y-%m-%d')
            match_score = record_item[0]['match_score']
            item = record_title, record_value, record_holder, record_date, match_score
        else:
            if record_function:
                record_minimum_requirement = await record_function(record_minimum_requirement)
            item = record_title, record_minimum_requirement, "-", "-", "-"
        records_as_tuples.append(item)
    records_as_tuples = sorted(records_as_tuples, reverse=True, key=lambda x: x[3])
    column_titles = ["Record name", "Value", "Record holder", "Record date", "Match score"]
    table = tablemaker(column_titles, records_as_tuples)
    msg = ("```" + table + "```")
    if len(msg) > 2000:
        widest_record_title, widest_record_value, widest_record_holder, = widest_in_list_of_tuples(records_as_tuples, 0), widest_in_list_of_tuples(records_as_tuples, 1), max([widest_in_list_of_tuples(records_as_tuples, 2),len("Record holder")])
        table_first_half, table_second_half = records_as_tuples[:len(records_as_tuples)//2], records_as_tuples[len(records_as_tuples)//2:] #todo implement properly
        await message.channel.send("```" + tablemaker(column_titles, table_first_half, column_widths=[widest_record_title, widest_record_value, widest_record_holder,15,10]) + "```")
        await asyncio.sleep(.5)
        await message.channel.send("```" + tablemaker(column_titles, table_second_half, column_widths=[widest_record_title, widest_record_value, widest_record_holder,15,10]) + "```")
    else:
        await message.channel.send(msg)


async def cmd_parse_records_of_past_matches(client, message, arg):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await message.channel.send("You're not allowed to use this command.")
        return
    if not arg:
        await message.channel.send("Usage: !faceit parsepastrecords <player nickname> <timestamp>")
        return
    args = arg.split(' ',1)
    if len(args) != 2:
        await message.channel.send("Usage: !faceit parsepastrecords <player nickname> <timestamp>")
        return
    nickname, timestamp = args
    player_guid = await faceit_db.get_guid_by_nickname(nickname)
    if not player_guid:
        await message.channel.send("Unknown player. Player must be in the database.")
        return

    bot_message = await message.channel.send("Processing..")
    matches = await faceit_api.player_match_history(player_guid, timestamp)
    matches = await fc.get_combined_match_data(matches)
    if matches:
        await fr.handle_records(player_guid, matches, message.guild.id)
        await bot_message.edit(content="%s matches processed for player %s" % (len(matches), nickname))
        return
    if not matches:
        await bot_message.edit(content="No matches found with the given timestamp.")
        return


async def cmd_add_faceit_channel(client, message, arg):
    if not arg:
        await message.channel.send('You must specify a channel name.')
        return
    guild_id = message.guild.id
    channel_id = await get_channel_id(client, arg)
    if not channel_id:
        await message.channel.send('No such channel.')
        return
    else:
        await faceit_db.update_faceit_channel(guild_id, str(channel_id))
        await message.channel.send('Faceit spam channel added.')
        return


async def get_faceit_guid(faceit_nickname):
    user = await faceit_api.user(faceit_nickname)
    return user.get("player_id", None)


async def get_channel_id(client, user_channel_name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == user_channel_name.lower():
            return channel.id
    return False  # If channel doesn't exist


async def get_player_aliases_string(faceit_guid, faceit_nickname):
    aliases_query_result = await faceit_db.get_player_aliases(faceit_guid)
    if aliases_query_result:
        alias_add_date = await faceit_db.get_player_add_date(faceit_guid)
        alias_string = ''
        for record in aliases_query_result:
            alias = record['faceit_nickname']
            until_date = record['created'].date()
            date_string = await get_alias_duration_string(alias_add_date, until_date)
            if alias != faceit_nickname:
                alias_string += alias + date_string + ', '
            alias_add_date = record['created'].date()
        return alias_string[::-1].replace(",", "", 1)[::-1]
    else:
        return '-'


async def get_user_stats_from_api_by_id(player_id):
    try:
        user = await faceit_api.user_by_id(player_id)
        player_id = user.get("player_id")
        last_activity = await fc.latest_match_timestamp(player_id)
    except NotFound as e:
        log.error(str(e))
        return None, None, None, None, None
    except UnknownError as e:
        log.error("Unknown error: {0}".format(str(e)))
        return None, None, None, None, None

    csgo = user.get("games", {}).get("csgo", {})
    nickname = user.get("nickname", None)  # Is this even needed
    skill_level = csgo.get("skill_level", None)
    csgo_elo = csgo.get("faceit_elo", None)
    ranking = await faceit_api.ranking(player_id) if csgo_elo else None
    return csgo_elo, skill_level, nickname, ranking, last_activity


async def get_alias_duration_string(alias_add_date, until_date):
    if alias_add_date == until_date:
        return (" *(%s)*" % until_date)
    else:
        return (" *(%s-%s)*" % (alias_add_date, until_date))


async def get_faceit_leaderboard(guild_id):
    toplist = []
    ranking = await faceit_db.get_toplist_from_db(guild_id)
    if not ranking:
        return None, None
    for item in ranking:
        eu_ranking, faceit_nickname, csgo_elo, skill_level, last_entry_time, player_last_played = item
        if not eu_ranking:
            continue
        new_item = eu_ranking, faceit_nickname, csgo_elo, skill_level, await get_last_seen_string(
            player_last_played)
        toplist.append(new_item)
    toplist_string = tablemaker(['EU RANKING', 'NAME', 'CS:GO ELO', 'SKILL LEVEL', 'LAST SEEN'],
                                             toplist)
    return toplist_string + (
            '\nLast changed: %s' % to_utc(as_helsinki(
        last_entry_time)).strftime("%d/%m/%y %H:%M")), len(toplist)


async def get_user_stats_from_api_by_nickname(client, message, faceit_nickname):
    try:
        user = await faceit_api.user(faceit_nickname)
        player_id = user.get("player_id")
        last_activity = await fc.latest_match_timestamp(player_id)
    except NotFound as e:
        log.error(str(e))
        if client and message:
            await message.channel.send(str(e))
        return None, None, None, None, None, None
    except UnknownError as e:
        log.error("Unknown error: {0}".format(str(e)))
        if client and message:
            await message.channel.send("Unknown error")
        return None, None, None, None, None, None

    csgo = user.get("games", {}).get("csgo", {})
    nickname = user.get("nickname", None)  # Is this even needed
    skill_level = csgo.get("skill_level", None)
    csgo_elo = csgo.get("faceit_elo", None)
    faceit_url = user.get("faceit_url", None)
    if faceit_url:
        faceit_url = faceit_url.format(lang='en')
    ranking = await faceit_api.ranking(player_id) if csgo_elo else None
    return csgo_elo, skill_level, nickname, ranking, last_activity, faceit_url


async def private_faceit_commands(client, message, arg):
    infomessage = "Available private faceit commands: " \
                  "```" \
                  "\n!faceit + " \
                  "\n<stats> <faceit nickname>" \
                  "```"
    try:
        arg, secondarg = arg.split(' ', 1)
    except ValueError:
        secondarg = None
    arg = arg.lower()
    if arg == 'stats':
        await cmd_faceit_stats(client, message, secondarg)
        return
    else:
        await message.channel.send(infomessage)
        return


async def get_last_seen_string(last_entry_time_string):
    entry_time = to_utc(as_helsinki(last_entry_time_string))
    now = to_utc(as_helsinki(datetime.now()))
    difference_in_days = (now - entry_time).days
    if difference_in_days == 0:
        return 'Today'
    elif abs(difference_in_days) == 1:
        return 'Yesterday'
    else:
        return str(abs(difference_in_days)) + ' Days ago'


def register():
    return {
        'faceit': cmd_faceit_commands,
    }