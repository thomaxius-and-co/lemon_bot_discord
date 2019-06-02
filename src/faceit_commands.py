import aiohttp
import asyncio
import util
import logger
import inspect
import database as db
import discord
import faceit_api
from faceit_api import NotFound, UnknownError
import columnmaker
from time_util import as_helsinki, to_utc, as_utc, to_helsinki
from datetime import datetime, timedelta
from util import pmap
import random

NOT_A_PM_COMMAND_ERROR = "This command doesn't work in private chat."

log = logger.get("FACEIT")

async def cmd_faceit_stats(client, message, faceit_nickname):
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname to search for.")
        return
    csgo_elo, skill_level, csgo_name, ranking_eu, last_played, faceit_url = await get_user_stats_from_api_by_nickname(client, message, faceit_nickname)
    log.info("%s, %s, %s, %s, %s, %s)" % (csgo_elo, skill_level, csgo_name, ranking_eu, last_played, faceit_url))
    aliases_string = "\n**Previous nicknames**: %s" % await get_player_aliases_string(await get_faceit_guid(faceit_nickname), faceit_nickname)
    if csgo_name:
        msg = "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**EU ranking**: %s\n**CS:GO Elo**: %s\n**Skill level**: %s\n**Last played**: %s%s\n**Faceit url**: %s" % (
                                  faceit_nickname, csgo_name, ranking_eu, csgo_elo, skill_level, to_utc(as_helsinki(datetime.fromtimestamp(last_played))).strftime("%d/%m/%y %H:%M") if last_played else '-', aliases_string, faceit_url)
        await client.send_message(message.channel, msg[:2000])

async def get_player_aliases_string(faceit_guid, faceit_nickname):
    aliases_query_result = await get_player_aliases(faceit_guid)
    if aliases_query_result:
        alias_add_date = await get_player_add_date(faceit_guid)
        alias_string = ''
        for record in aliases_query_result:
            alias = record['faceit_nickname']
            until_date = record['created'].date()
            date_string = await get_alias_duration_string(alias_add_date, until_date)
            if alias != faceit_nickname:
                alias_string += alias + date_string + ', '
            alias_add_date = record['created'].date()
        return alias_string[::-1].replace(",","",1)[::-1]
    else:
        return '-'



async def get_alias_duration_string(alias_add_date, until_date):
    if alias_add_date == until_date:
        return (" *(%s)*" % until_date)
    else:
        return (" *(%s-%s)*" % (alias_add_date, until_date))

async def get_player_add_date(faceit_guid):
    query_result  = await db.fetchval("""        
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
                  "```"
    if message.channel.is_private:
        await private_faceit_commands(client, message, arg)
        return
    if not arg:
        await client.send_message(message.channel, infomessage)
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
    else:
        await client.send_message(message.channel, infomessage)
        return


async def cmd_show_aliases(client, message, faceit_nickname):
    guild_players = await get_players_in_guild(message.server.id)
    for record in guild_players:
        if faceit_nickname == record['faceit_nickname']:
                player_guid = await get_faceit_guid(faceit_nickname)
                if player_guid:
                    aliases_query_result = await get_player_aliases(player_guid)
                    if aliases_query_result: #This is a bit lazy
                        alias_string = await get_player_aliases_string(player_guid, faceit_nickname)
                        msg = "**%s** has the following aliases: %s" % (faceit_nickname, alias_string)
                        await client.send_message(message.channel, msg[:2000]) #todo: replace this with some sort of 'long message splitter'
                        return
                    else:
                        await client.send_message(message.channel, "**%s** has no aliases." % (
                        faceit_nickname))
                        return
    await client.send_message(message.channel, "No such player in the server, use !faceit listusers.")


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
        await client.send_message(message.channel, infomessage)
        return


async def latest_match_timestamp(player_id):
    json = await faceit_api.player_history(player_id)
    matches = json.get("items")
    timestamps = flat_map(lambda m: [m.get("started_at"), m.get("finished_at")], matches)
    return max_or(timestamps, None)


async def get_user_stats_from_api_by_id(player_id):
    try:
        user = await faceit_api.user_by_id(player_id)
        player_id = user.get("player_id")
        last_activity = await latest_match_timestamp(player_id)
    except NotFound as e:
        log.error(str(e))
        return None, None, None, None, None
    except UnknownError as e:
        log.error("Unknown error: {0}".format(str(e)))
        return None, None, None, None, None

    csgo = user.get("games", {}).get("csgo", {})
    nickname = user.get("nickname", None) # Is this even needed
    skill_level = csgo.get("skill_level", None)
    csgo_elo = csgo.get("faceit_elo", None)
    ranking = await faceit_api.ranking(player_id) if csgo_elo else None
    return csgo_elo, skill_level, nickname, ranking, last_activity


async def get_user_stats_from_api_by_nickname(client, message, faceit_nickname):
    try:
        user = await faceit_api.user(faceit_nickname)
        player_id = user.get("player_id")
        last_activity = await latest_match_timestamp(player_id)
    except NotFound as e:
        log.error(str(e))
        if client and message:
            await client.send_message(message.channel, str(e))
        return None, None, None, None, None, None
    except UnknownError as e:
        log.error("Unknown error: {0}".format(str(e)))
        if client and message:
            await client.send_message(message.channel, "Unknown error")
        return None, None, None, None, None, None

    csgo = user.get("games", {}).get("csgo", {})
    nickname = user.get("nickname", None) # Is this even needed
    skill_level = csgo.get("skill_level", None)
    csgo_elo = csgo.get("faceit_elo", None)
    faceit_url = user.get("faceit_url", None)
    if faceit_url:
        faceit_url = faceit_url.format(lang='en')
    ranking = await faceit_api.ranking(player_id) if csgo_elo else None
    return csgo_elo, skill_level, nickname, ranking, last_activity, faceit_url


async def get_faceit_guid(faceit_nickname):
    user = await faceit_api.user(faceit_nickname)
    return user.get("player_id", None)


async def cmd_add_faceit_user_into_database(client, message, faceit_nickname):
    guild_id = message.server.id
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname for the user to be added, "
                                                   "for example: !faceit adduser Jallu-rce")
        return
    try:
        faceit_guid = await get_faceit_guid(faceit_nickname)
        await add_faceit_user_into_database(faceit_nickname, faceit_guid)
        if not await assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
            await client.send_message(message.channel, "%s is already in the database." % faceit_nickname)
        else:
            await client.send_message(message.channel, "Added %s into the database." % faceit_nickname)
            log.info("Adding stats for added player %s, guid %s" % (faceit_nickname, faceit_guid))
            current_elo, skill_level, csgo_name, ranking, last_played = await get_user_stats_from_api_by_id(faceit_guid)
            if not current_elo or not ranking:  # Currently, only EU ranking is supported
                return
            if not (await get_player_aliases(faceit_guid)):
                await add_nickname(faceit_guid, csgo_name)
            else:
                log.info("Not adding a nickname for user since he already has one")
                await(do_nick_change_check(faceit_guid, csgo_name, await get_player_current_database_nickname(faceit_guid)))
            await insert_data_to_player_stats_table(faceit_guid, current_elo, skill_level, ranking)

    except NotFound as e:
        await client.send_message(message.channel, str(e))
    except UnknownError as e:
        await client.send_message(message.channel, "Unknown error")


async def assign_faceit_player_to_server_ranking(guild_id, faceit_guid):
    already_in_db = await db.fetchval(
        "SELECT count(*) = 1 FROM faceit_guild_ranking WHERE guild_id = $1 AND faceit_guid = $2", guild_id, faceit_guid)
    if already_in_db == True:
        return False

    await db.execute("INSERT INTO faceit_guild_ranking (guild_id, faceit_guid) VALUES ($1, $2)", guild_id, faceit_guid)
    return True

async def add_faceit_user_into_database(faceit_nickname, faceit_guid):
    await db.execute("INSERT INTO faceit_player (faceit_nickname, faceit_guid) VALUES ($1, $2) ON CONFLICT DO NOTHING", faceit_nickname, faceit_guid)

async def update_faceit_channel(guild_id, channel_id):
    await db.execute("""
        INSERT INTO faceit_notification_channel (guild_id, channel_id) VALUES ($1, $2)
        ON CONFLICT (guild_id) DO UPDATE SET channel_id = EXCLUDED.channel_id
    """, guild_id, channel_id)

async def get_channel_id(client, user_channel_name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == user_channel_name.lower():
            return channel.id
    return False  # If channel doesn't exist


async def cmd_add_faceit_channel(client, message, arg):
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


async def cmd_del_faceit_user(client, message, arg):
    guild_id = message.server.id
    if not arg:
        await client.send_message(message.channel,
                                  "You must specify faceit nickname, or an ID to delete, eq. !faceit deluser 1. "
                                  "Use !faceit list to find out the correct ID.")
        return
    guild_faceit_players_entries = await get_players_in_guild(message.server.id)
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
                await client.send_message(message.channel,
                                          "Faceit user %s succesfully deleted." % entry['faceit_nickname'])
                return
        await client.send_message(message.channel, "No such user in list. Use !faceit listusers to display a list of ID's.")
        return


async def cmd_list_faceit_users(client, message, _):
    guild_faceit_players_entries = await get_players_in_guild(message.server.id)
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


async def elo_notifier_task(client):
    fetch_interval = 60
    while True:
        await asyncio.sleep(fetch_interval)
        try:
            await check_faceit_elo(client)
        except Exception as e:
            log.error("Failed to check faceit stats: ")
            await util.log_exception(log)


async def get_match_stats(match_id):
    try:
        return await faceit_api.match(match_id)
    except NotFound as e:
        log.error(e)
        return None


async def get_matches(player_guid, from_timestamp, to_timestamp=None):
    try:
        return await faceit_api.player_match_history(player_guid, from_timestamp, to_timestamp)
    except NotFound as e:
        log.error(e)
        return None


async def get_match_info(match_id):
    try:
        return await faceit_api.match_stats(match_id)
    except NotFound as e:
        log.error(e)
        return None

async def get_length_string(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '**Match length**: {:d}:{:02d}:{:02d}'.format(h, m, s)


async def get_score_string(match):
    overtime_score = None
    map = match[0].get("round_stats").get("Map")
    score = match[0].get("round_stats").get("Score").replace(' / ', '-')
    first_half_score = "%s-%s" % (match[0].get("teams")[0].get("team_stats").get("First Half Score"), match[0].get("teams")[1].get("team_stats").get("First Half Score"))
    second_half_score = "%s-%s" % (match[0].get("teams")[0].get("team_stats").get("Second Half Score"), match[0].get("teams")[1].get("team_stats").get("Second Half Score"))
    total_rounds = int(match[0].get("round_stats").get("Rounds"))
    if total_rounds > 30:
        overtime_score = "%s-%s" % (
            match[0].get("teams")[0].get("team_stats").get("Overtime score"), match[0].get("teams")[1].get("team_stats").get("Overtime score"))
    if overtime_score:
        score_string = ("**Map**: %s **score**: %s (%s, %s, %s)" % (map, score, first_half_score, second_half_score, overtime_score))
    else:
        score_string = ("**Map**: %s **score**: %s (%s, %s)" % (map, score, first_half_score, second_half_score))
    return score_string




async def get_info_strings(match, player_guid):
    try:
        match_details = await get_match_info(match.get("match_id"))
        if not match_details:
            return None, None
        score_string = await get_score_string(match_details)
        player_stats_string = await get_player_stats(match, match_details, player_guid)
        return score_string, player_stats_string
    except NotFound as e:
        log.error(e, 'Ghost match')
        return None, None



async def get_player_rank_in_team(players_list, player_dict):
    return sorted(players_list, reverse=True, key=lambda x: int(x.get("player_stats").get("Kills"))).index(player_dict) + 1


async def get_player_highlight(nickname, assists, deaths, headshots, headshots_perc, kd_ratio, kr_ratio, kills, mvps, result, penta_kills, quadro_kills, triple_kills, rounds, match_length):
    base_string = "**Match highlight(s)**:"
    highlight_string = ""
    kill_highlights = {
        'PENTA_KILLS': {'condition':(penta_kills >= 1), 'description': "**%s** had **%s** penta kill(s)" % (nickname, penta_kills)},
        'QUADRO_KILLS': {'condition':(quadro_kills >= 1), 'description': "**%s** had **%s** quadro kill(s)" % (nickname, quadro_kills)},
        'TRIPLE_KILLS': {'condition': (triple_kills >= 5), 'description': "**%s** had **%s** triple kill(s)" % (nickname, triple_kills)}
    }

    random_highlights = {
        'ASSIST_KING': {'condition':(assists > kills), 'description': " **%s** had more assists (%s) than kills (%s)" % (nickname, assists, kills)},
        'MANY_KILLS_AND_LOSE' : {'condition':((kills >= 30) and (result == 0)), 'description': " **%s** had %s kills and still lost the match" % (nickname, kills)},
        'HEADSHOTS_KING': {'condition':(headshots_perc >= 65), 'description':" **%s** had **%s** headshot percentage" % (nickname, headshots_perc)},
        'MANY_KILLS_NO_MVPS': {'condition':(kr_ratio >= 0.7) and (mvps == 0), 'description':" **%s** had 0 mvps but %s kills (%s per round)" % (nickname, kills, kr_ratio)},
        'BAD_STATS_STILL_WIN': {'condition':(kills <= 5) and (result == 1), 'description':" **%s** won the match even though he was %s-%s-%s" % (nickname, kills, assists, deaths)},
        'DIED_EVERY_ROUND': {'condition': (deaths == rounds), 'description':" **%s** died every round (%s times)" % (nickname, deaths)},
        'LONG_MATCH': {'condition': ((match_length / rounds) > 110), 'description':"Rounds had an average length of **{0:.3g}** minutes".format((match_length / 60) / rounds)}
    }

    for x in kill_highlights:
        condition = kill_highlights.get(x).get('condition')
        if condition:
            highlight_string += base_string + kill_highlights.get(x).get("description")
            break

    occured_highlights = [x for x in random_highlights if random_highlights.get(x).get('condition')]
    if not occured_highlights and not highlight_string:
        return ""
    else:
        chosen_highlight = random_highlights.get(random.choice(occured_highlights)).get("description")
        if highlight_string:
            return highlight_string + " and " + chosen_highlight.replace("**" + nickname + "**", "they")
        else:
            return base_string + chosen_highlight


async def get_player_stats(match, match_details, player_guid):
    teams = match_details[0].get("teams")
    for team in teams:
        for player in team.get("players"):
            if player.get('player_id') == player_guid:
                rounds = match_details[0].get("round_stats").get("Rounds")
                match_length = match.get("finished_at") - match.get("started_at")
                player_stats = player.get("player_stats")
                player_rank = await get_player_rank_in_team(team.get("players"), player)
                nickname, assists, deaths, headshots, headshots_perc, kd_ratio, kr_ratio, kills, mvps, penta_kills, quadro_kills, triple_kills, result = player_stats.get("Nickname"), int(
                    player_stats.get("Assists")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Deaths")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Headshot")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Headshots %")), \
                                                                                                                                               float(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "K/D Ratio")), \
                                                                                                                                               float(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "K/R Ratio")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Kills")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "MVPs")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Penta Kills")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Quadro Kills")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Triple Kills")), \
                                                                                                                                               int(
                                                                                                                                                   player_stats.get(
                                                                                                                                                       "Result")),
                highlight_string = await get_player_highlight(nickname, assists, deaths, headshots, headshots_perc, kd_ratio, kr_ratio, kills, mvps, result, penta_kills, quadro_kills, triple_kills, rounds, match_length)
                return "**Player stats:** #%s %s-%s-%s (%s kdr)%s" % (player_rank, kills, assists, deaths, kills, ("\n" + highlight_string if highlight_string else ''))
    return ""




async def get_match_length_string(match):
    started_at = match.get("started_at")
    finished_at = match.get("finished_at")
    return await get_length_string(finished_at - started_at)


async def get_match_info_string(player_guid, from_timestamp):
    matches = await get_matches(player_guid, int(from_timestamp))
    if not matches:
        return None
    i = 1
    match_info_string = ""
    for match in matches:
        score, stats = await get_info_strings(match, player_guid)
        if not score or not stats:
            continue
        match_details = await get_match_stats(match.get("match_id"))
        match_length_string = await get_match_length_string(match_details)
        match_info_string += "%s %s %s %s\n" % (("**Match %s**" % i) if len(matches) > 1 else "**Match**", score, stats, match_length_string)
        i += 1
        if i > 10: # Only fetch a max of 10 matches
            break
    if not match_info_string:
        return match_info_string
    else:
        return "*" + match_info_string.rstrip("\n") + "*"

async def check_faceit_elo(client):
    log.info('Faceit stats checking started')
    faceit_players = await get_all_players()
    if not faceit_players:
        return
    old_toplist_dict = await get_server_rankings_per_guild()
    log.info("Fetching stats from FACEIT for %s players" % len(faceit_players))
    player_ids = list(map(lambda p: p["faceit_guid"], faceit_players))
    api_responses = await fetch_players_batch(player_ids)
    for record in faceit_players:
        player_guid = record['faceit_guid']
        player_database_nick = record['faceit_nickname']
        player_stats = await get_faceit_stats_of_player(player_guid)
        if player_stats:
            current_elo, skill_level, csgo_name, ranking, last_played = api_responses[player_guid]
            await do_nick_change_check(player_guid, csgo_name, player_database_nick)
            if not current_elo or not ranking or not player_stats['faceit_ranking'] or not player_stats[
                'faceit_ranking']:  # Currently, only EU ranking is supported
                continue
            if current_elo != player_stats['faceit_elo']:
                await insert_data_to_player_stats_table(player_guid, current_elo, skill_level, ranking)

                for channel_id, custom_nickname in await channels_to_notify_for_user(player_guid):
                    log.info("Notifying channel %s", channel_id)
                    await spam_about_elo_changes(client, record['faceit_nickname'], channel_id,
                                                 current_elo, player_stats['faceit_elo'], skill_level,
                                                 player_stats['faceit_skill'], (
                                                     ' "' + custom_nickname + '"' if custom_nickname else ''), await get_match_info_string(player_guid, to_utc(player_stats['changed']).timestamp()))
        else:
            current_elo, skill_level, csgo_name, ranking, last_played = await get_user_stats_from_api_by_id(player_guid)
            if not current_elo or not ranking:  # Currently, only EU ranking is supported
                continue
            await insert_data_to_player_stats_table(player_guid, current_elo, skill_level, ranking)
    await compare_toplists(client, old_toplist_dict)
    log.info('Faceit stats checked')


async def fetch_players_batch(player_ids):
    responses = await pmap(get_user_stats_from_api_by_id, player_ids)
    return dict(zip(player_ids, responses))


async def do_nick_change_check(guid, api_player_name, database_player_name):
    log.info("Checking nickname changes for user %s %s" % (guid, database_player_name))
    if api_player_name != database_player_name:
        log.info("Nickname change detected for user %s: old %s, new %s" % (guid, database_player_name, api_player_name))
        await update_nickname(guid, api_player_name)
    else:
        log.info("No nickname changes detected for user %s " % guid)
        return


async def update_nickname(faceit_guid, api_player_name):
    async with db.transaction() as tx:
        await tx.execute("INSERT INTO faceit_aliases (faceit_guid, faceit_nickname) VALUES ($1, $2)", faceit_guid, api_player_name)
        await tx.execute("UPDATE faceit_player SET faceit_nickname = $1 WHERE faceit_guid = $2", api_player_name, faceit_guid)
    log.info("Updated nickname %s for user %s" % (api_player_name, faceit_guid))


async def add_nickname(faceit_guid, api_player_name):
    async with db.transaction() as tx:
        await tx.execute("INSERT INTO faceit_aliases (faceit_guid, faceit_nickname) VALUES ($1, $2)", faceit_guid, api_player_name)
    log.info("Added new nickname %s for user %s" % (api_player_name, faceit_guid))


async def compare_toplists(client, old_toplist_dict):
    new_toplist_dict = await get_server_rankings_per_guild()
    log.info("Comparing toplists")
    for key in old_toplist_dict:
        spam_channel_id = await get_spam_channel_by_guild(key)
        if not spam_channel_id:  # Server doesn't like to be spammed, no need to do any work
            continue
        old_toplist_sorted = sorted(old_toplist_dict.get(key), key=lambda x: x[2])
        new_toplist_sorted = sorted(new_toplist_dict.get(key), key=lambda x: x[2])
        if len(old_toplist_sorted) != len(new_toplist_sorted):
            log.info("Someone was added to faceit database, not making toplist comparision.")
            continue
        elif old_toplist_sorted == new_toplist_sorted:
            log.info("No changes in rankings, not making comparsions")
            continue
        else:
            await check_and_spam_rank_changes(client, old_toplist_sorted[:11], new_toplist_sorted[:11], spam_channel_id)


async def check_and_spam_rank_changes(client, old_toplist, new_toplist, spam_channel_id):
    msg = ""
    for item_at_oldlists_index, item_at_newlists_index in zip(old_toplist,
                                                              new_toplist):  # Compare each item of both lists side to side
        name_in_old_item = item_at_oldlists_index[0]  # Name of player in old toplist
        name_in_new_item = item_at_newlists_index[0]  # Name of player in the same index in new toplist

        if name_in_old_item != name_in_new_item:  # If the players don't match, it means player has dropped in the leaderboard
            player_new_rank_item = [item for item in new_toplist if
                                    item[0] == name_in_old_item and item[2] != item_at_oldlists_index[
                                        2]]  # Find the player's item in the new toplist, but only if their ELO has changed aswell
            if player_new_rank_item:  # If the player is found in new toplist
                old_rank = old_toplist.index(
                    item_at_oldlists_index) + 1  # Player's old position (rank) in the old toplist
                new_rank = new_toplist.index(
                    player_new_rank_item[0]) + 1  # Player's new position (rank) in the new toplist
                old_elo = item_at_oldlists_index[1]
                new_elo = player_new_rank_item[0][1]
                player_name = player_new_rank_item[0][0]
                if (old_rank > new_rank) and (new_elo > old_elo):
                    msg += "**%s** rose in server ranking! old rank **#%s**, new rank **#%s**\n" % (
                    player_name, old_rank, new_rank)
                elif (old_rank < new_rank) and (old_elo > new_elo):
                    msg += "**%s** fell in server ranking! old rank **#%s**, new rank **#%s**\n" % (
                    player_name, old_rank, new_rank)
    if msg:
        log.info('Attempting to spam channel %s with the following message: %s', spam_channel_id, msg)
        channel = discord.Object(id=spam_channel_id)
        util.threadsafe(client, client.send_message(channel, msg))
        await asyncio.sleep(.25)
    log.info("Rank changes checked")


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


async def cmd_add_faceit_nickname(client, message, arg):
    guild_id = message.server.id
    errormessage = "Usage: !faceit addnick <faceit user> <nickname>\n for example: !faceit addnick rce jallulover69"
    if not arg:
        await client.send_message(message.channel, errormessage)
        return
    try:
        faceit_name, custom_nickname = arg.split(' ', 1)
    except ValueError:
        await client.send_message(message.channel, errormessage)
        return
    if not faceit_name or not custom_nickname:
        await client.send_message(message.channel, errormessage)
        return
    for player in await get_players_in_guild(guild_id):
        if player['faceit_nickname'] == faceit_name:
            await set_faceit_nickname(guild_id, faceit_name, custom_nickname)
            await client.send_message(message.channel, "Nickname %s set for %s." % (custom_nickname, faceit_name))
            return
    await client.send_message(message.channel, "Player %s not found in database. " % faceit_name)


async def spam_about_elo_changes(client, faceit_nickname, spam_channel_id, current_elo, elo_before, current_skill,
                                 skill_before, custom_nickname, match_info_string):
    await asyncio.sleep(0.1)
    channel = discord.Object(id=spam_channel_id)
    message = None

    if skill_before < current_skill:
        util.threadsafe(client, client.send_message(channel,
                                                    '**%s%s** gained **%s** elo and a new skill level! (Skill level %s -> %s, Elo now: %s)\n%s' % (
                                                    faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                    skill_before, current_skill, current_elo, match_info_string)))
        return
    elif skill_before > current_skill:
        util.threadsafe(client, client.send_message(channel,
                                                    '**%s%s** lost **%s** elo and lost a skill level! (Skill level %s -> %s, Elo now: %s)\n%s' % (
                                                    faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                    skill_before, current_skill, current_elo, match_info_string)))
        return
    elif current_elo > elo_before:
        util.threadsafe(client, client.send_message(channel, '**%s%s** gained **%s** elo! (%s -> %s)\n%s' % (
        faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo, match_info_string)))
        return
    elif elo_before > current_elo:
        util.threadsafe(client, client.send_message(channel, '**%s%s** lost **%s** elo! (%s -> %s)\n%s' % (
        faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo, match_info_string)))
        return


async def get_faceit_leaderboard(guild_id):
    toplist = []
    ranking = await get_toplist_from_db(guild_id)
    if not ranking:
        return None, None
    for item in ranking:
        eu_ranking, faceit_nickname, csgo_elo, skill_level, last_entry_time, player_last_played = item
        if not eu_ranking:
            continue
        new_item = eu_ranking, faceit_nickname, csgo_elo, skill_level, await get_last_seen_string(
            player_last_played)
        toplist.append(new_item)
    toplist_string = columnmaker.columnmaker(['EU RANKING', 'NAME', 'CS:GO ELO', 'SKILL LEVEL', 'LAST SEEN'],
                                             toplist)
    return toplist_string + (
                '\nLast changed: %s' % to_utc(as_helsinki(
            last_entry_time)).strftime("%d/%m/%y %H:%M")), len(toplist)


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


async def get_server_rankings_per_guild():
    ranking = await get_toplist_per_guild_from_db()
    ranking_dict = {}
    for item in ranking:
        guild_id, nickname, elo, ranking = item
        if guild_id not in ranking_dict:
            ranking_dict.update({guild_id: [[nickname, elo, ranking]]})
        else:
            dict_item = ranking_dict.get(guild_id)
            dict_item.append([nickname, elo, ranking])
    return ranking_dict


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


async def cmd_do_faceit_toplist(client, message, input):
    if message.channel.is_private:
        await client.send_message(message.channel, 'This command does not work on private servers.')
        return
    toplist, amountofpeople = await get_faceit_leaderboard(message.server.id)
    if not toplist or not amountofpeople:
        await client.send_message(message.channel,
                                  'No faceit players have been added to the database, or none of them have rank.')
        return
    title = 'Top %s ranked faceit CS:GO players:' % (amountofpeople)
    await client.send_message(message.channel, ('```%s \n' % title + toplist + '```'))


async def get_all_players():
    return await db.fetch("""
        SELECT faceit_guid, faceit_nickname FROM faceit_player
        WHERE faceit_guid IN (SELECT DISTINCT faceit_guid FROM faceit_guild_ranking)
        ORDER BY id ASC
    """)

async def get_players_in_guild(guild_id):
    return await db.fetch("SELECT * FROM faceit_guild_ranking JOIN faceit_player USING (faceit_guid) WHERE guild_id = $1 ORDER BY id ASC", guild_id)

def register(client):
    util.start_task_thread(elo_notifier_task(client))
    return {
        'faceit': cmd_faceit_commands,
    }


def flat_map(func, xs):
    from itertools import chain
    return list(chain.from_iterable(map(func, xs)))


def max_or(xs, fallback):
    return max(xs) if len(xs) > 0 else fallback

# todo: replace with named arguments
def tests():
    loop = asyncio.get_event_loop()
    tests = {
        "ASSISTS_KING" : {"args": ["rce", 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 23, 1], "expected_result": "**Match highlight(s)**: **rce** had more assists (10) than kills (0)"},
        "MANY_KILLS_AND_LOSE": {"args": ["rce", 0, 0, 0, 0, 0, 0, 31, 0, 0, 0, 0,0, 23, 1], "expected_result": "**Match highlight(s)**: **rce** had 31 kills and still lost the match"},
        "HEADSHOTS_KING": {"args": ["rce", 0, 0, 0, 66, 0, 0, 0, 0, 0, 0, 0, 0, 23, 1],"expected_result": "**Match highlight(s)**: **rce** had **66** headshot percentage"},
        "MANY_KILLS_NO_MVPS": {"args": ["rce", 0, 0, 0, 0, 0, 0.8, 20, 0, 0, 0, 0, 0, 23, 1],"expected_result": "**Match highlight(s)**: **rce** had 0 mvps but 20 kills (0.8 per round)"},
        "BAD_STATS_STILL_WIN": {"args": ["rce", 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 23, 1],"expected_result": "**Match highlight(s)**: **rce** won the match even though he was 0-0-0"},
        "DIED_EVERY_ROUND": {"args": ["rce", 0, 23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 23, 1],"expected_result": "**Match highlight(s)**: **rce** died every round (23 times)"},
        "LONG_MATCH": {"args": ["rce", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 3500],"expected_result": "**Match highlight(s)**:Rounds had an average length of **1.94** minutes"},
        "PENTA_KILLS_AND_MANY_KILLS_AND_LOSE": {"args": ["rce", 0, 0, 0, 0, 0, 0, 31, 0, 0, 10, 0, 0, 23, 1], "expected_result": "**Match highlight(s)**:**rce** had **10** penta kill(s) and  they had 31 kills and still lost the match"},
    }
    for test_name in tests:
        test_args, test_expected_result = tests.get(test_name).get("args"), tests.get(test_name).get("expected_result")
        result = loop.run_until_complete(get_player_highlight(*test_args))
        if result != test_expected_result:
            log.error("Test %s failed! Expected result was %s but got: %s" % (test_name, test_expected_result, result))
        else:
            log.info("Test OK. Result: %s" % result)