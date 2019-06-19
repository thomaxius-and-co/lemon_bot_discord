
import faceit_db_functions as faceit_db
import asyncio
import util
import logger
import discord
import faceit_api
from faceit_api import NotFound
from time_util import to_utc
from util import pmap
import faceit_highlights as fh
import faceit_common as fc
import datetime

NOT_A_PM_COMMAND_ERROR = "This command doesn't work in private chat."

log = logger.get("FACEIT")
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
    faceit_players = await faceit_db.get_all_players()
    if not faceit_players:
        return
    old_toplist_dict = await get_server_rankings_per_guild()
    log.info("Fetching stats from FACEIT for %s players" % len(faceit_players))
    player_ids = list(map(lambda p: p["faceit_guid"], faceit_players))
    api_responses = await fetch_players_batch(player_ids)
    for record in faceit_players:
        player_guid = record['faceit_guid']
        player_database_nick = record['faceit_nickname']
        player_stats = await faceit_db.get_faceit_stats_of_player(player_guid)
        if player_stats:
            current_elo, skill_level, csgo_name, ranking, last_played = api_responses[player_guid]
            await fc.do_nick_change_check(player_guid, csgo_name, player_database_nick)
            if not current_elo or not ranking or not player_stats['faceit_ranking'] or not player_stats[
                'faceit_ranking']:  # Currently, only EU ranking is supported
                continue
            if current_elo != player_stats['faceit_elo']:
                await faceit_db.insert_data_to_player_stats_table(player_guid, current_elo, skill_level,
                                                                  ranking)

                for channel_id, custom_nickname in await faceit_db.channels_to_notify_for_user(player_guid):
                    channel = client.get_channel(channel_id)
                    log.info("Notifying channel %s", channel.id)
                    matches = await get_matches(player_guid, to_utc(player_stats['changed']).timestamp())
                    matches = await get_combined_match_data(matches)
                    if matches:
                        match_stats_string = await get_match_stats_string(player_guid, matches)
                        guild_id = channel.server.id
                        await handle_records(player_guid, matches, guild_id)
                        records_string = await get_record_string(player_guid, guild_id, matches)
                    else:
                        match_stats_string = ''
                        records_string = ''
                    await spam(client, record['faceit_nickname'], channel_id,
                                                 current_elo, player_stats['faceit_elo'], skill_level,
                                                 player_stats['faceit_skill'], (
                                                     ' "' + custom_nickname + '"' if custom_nickname else ''),
                                                 match_stats_string, records_string)

        else:
            current_elo, skill_level, csgo_name, ranking, last_played = await fc.get_user_stats_from_api_by_id(
                player_guid)
            if not current_elo or not ranking:  # Currently, only EU ranking is supported
                continue
            await faceit_db.insert_data_to_player_stats_table(player_guid, current_elo, skill_level,
                                                              ranking)
    await compare_toplists(client, old_toplist_dict)
    log.info('Faceit stats checked')

async def get_records_by_guild(guild_id):
    records = {
        'MOST_KILLS': {
            'message': 'Most kills in a match',
            'record_item': await faceit_db.top_kills(guild_id),
            'condition': '>',
            'minimum_requirement': 20,
            'identifier': 'kills'
        },
        'MOST_ASSISTS': {
            'message': 'Most assists in a match',
            'record_item': await faceit_db.top_assists(guild_id),
            'condition': '>',
            'minimum_requirement': 5,
            'identifier': 'assists'
        },
        'MOST_DEATHS': {
            'message': 'Most deaths in a match',
            'record_item': await faceit_db.top_deaths(guild_id),
            'condition': '>',
            'minimum_requirement': 20,
            'identifier': 'deaths'
        },
        'MOST_HEADSHOTS': {
            'message': 'Most headshots in a match',
            'record_item': await faceit_db.top_headshots(guild_id),
            'condition': '>',
            'minimum_requirement': 10,
            'identifier': 'headshots'
        },
        'BIGGEST_HEADSHOT_PERCENTAGE': {
            'message': 'Biggest headshot percentage',
            'record_item': await faceit_db.top_headshot_percentage(guild_id),
            'condition': '>',
            'minimum_requirement': 50,
            'identifier': 'headshot_percentage'
        },
        'MOST_MVPS': {
            'message': 'Most mvps in a match',
            'record_item': await faceit_db.top_mvps(guild_id),
            'condition': '>',
            'minimum_requirement': 5,
            'identifier': 'mvps'
        },
        'MOST_TRIPLE_KILLS': {
            'message': 'Most triple kills in a match',
            'record_item': await faceit_db.top_triple_kills(guild_id),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'triple_kills'
        },
        'MOST_QUADRO_KILLS': {
            'message': 'Most quadro kills in a match',
            'record_item': await faceit_db.top_quadro_kills(guild_id),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'quadro_kills'
        },
        'MOST_PENTA_KILLS': {
            'message': 'Most penta kills in a match',
            'record_item': await faceit_db.top_penta_kills(guild_id),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'penta_kills'
        },
        'BIGGEST_KD_RATIO': {
            'message': 'Biggest kd ratio in a match',
            'record_item': await faceit_db.top_kdr(guild_id),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'kd_ratio'
        },
        'BIGGEST_KR_RATIO': {
            'message': 'Biggest kills per round ratio in a match',
            'record_item': await faceit_db.top_kpr(guild_id),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'kr_ratio'
        },
        'BIGGEST_DPR_RATIO': {
            'message': 'Most deaths per round in a match',
            'record_item': await faceit_db.top_dpr(guild_id),
            'condition': '>',
            'minimum_requirement': 0.5,
            'identifier': 'dpr_ratio'
        },
        'LONGEST_MATCH_ROUNDS': {
            'message': 'Longest match by rounds',
            'record_item': await faceit_db.match_most_rounds(guild_id),
            'condition': '>',
            'minimum_requirement': 30,
            'identifier': 'total_rounds'
        },
        'LONGEST_MATCH_SECONDS': {
            'message': 'Longest match by rounds',
            'record_item': await faceit_db.match_most_rounds(guild_id),
            'condition': '>',
            'minimum_requirement': 3600,
            'identifier': 'match_length_seconds'
        },
        'WORST_KD_RATIO': {
            'message': 'Worst kd ratio in a match',
            'record_item': await faceit_db.worst_kd_ratio(guild_id),
            'minimum_requirement': 0.5,
            'condition': '<',
            'identifier': 'kr_ratio_worst'
        },
    }
    return records


async def get_record_string(player_guid, guild_id, matches):
    matches_sorted_by_time = sorted(matches.values(), reverse=True, key=lambda x: int(x.get("match_details").get("finished_at")))
    latest_match_timestamp = int(matches_sorted_by_time[0].get("match_details").get("finished_at"))
    current_records = await get_records_by_guild(guild_id)
    record_string = ""
    for record in current_records.values():
        record_item = record.get("record_item") # This is the item that comes from the DB
        if record_item:
            record_minimum_requirement = record.get("minimum_requirement")
            record_condition = record.get("condition")
            record_value = record_item[0][0]
            if (record_condition == '>' and not (record_value > record_minimum_requirement)) or (record_condition == '<' and not (record_value > record_minimum_requirement)):
                continue
            record_holder_guid = record_item[0]['faceit_guid']
            record_holder_name = record_item[0]['faceit_nickname']
            record_match_finished_at = record_item[0]['finished_at']
            if len(record_item) > 1:
                previous_record_value = record_item[1][0]
                if previous_record_value == record_value:
                    continue # Don't spam if record is same as before

                previous_record_holder_guid = record_item[1]['faceit_guid']
                previous_record_holder_name = record_item[1]['faceit_nickname']
                previous_record_string = "(previous record: %s by %s)" % (previous_record_value, previous_record_holder_name)
            else:
                previous_record_string = ""
            record_message = record.get("message")
            record_identifier = record.get("identifier")
            if player_guid == record_holder_guid and latest_match_timestamp >= record_match_finished_at:
                if record_string:
                    record_string += "%s (%s) %s\n" % (record_message, record_value, previous_record_string)
                else:
                    record_string = "%s broke the following records: %s (%s) %s\n" % (record_holder_name, record_message, record_value, previous_record_string)


    return record_string


async def handle_records(player_guid, matches_dict, guild_id):
    for match in matches_dict.values():
        match_details = match.get("match_details")
        match_stats = match.get("match_stats")
        competition_type = match_details.get("competition_type")
        competition_name = match_details.get("competition_name")
        if competition_type != 'matchmaking' or competition_name not in ['CS:GO 5v5 PREMIUM', 'CS:GO 5v5']:
            log.info("Match is not matchmaking, skipping..")
            continue
        best_of = int(match_stats.get("best_of"))
        match_id = match_stats.get("match_id")
        rounds = int(match_stats.get("round_stats").get("Rounds"))
        started_at = int(match_details.get("started_at"))
        finished_at = int(match_details.get("finished_at"))
        match_length_seconds = (finished_at - started_at) / best_of
        teams = match_stats.get("teams") # Get the two teams that played in the game
        for team in teams:
            players = team.get("players")
            for player in players:
                if player.get("player_id") == player_guid: # If player is in this team
                    added_timestamp = datetime.datetime.now()
                    win = True if int(team.get("team_stats").get("Team Win")) == 1 else False
                    player_team_rank = await get_player_rank_in_team(players, player)
                    player_team_first_half_score = int(team.get("team_stats").get("First Half Score"))
                    player_team_second_half_score = int(team.get("team_stats").get("Second Half Score"))
                    player_team_overtime_score = int(team.get("team_stats").get("Overtime score"))
                    kills = int(player.get("player_stats").get("Kills"))
                    assists = int(player.get("player_stats").get("Assists"))
                    deaths = int(player.get("player_stats").get("Deaths"))
                    headshots = int(player.get("player_stats").get("Headshot"))
                    headshot_percentage = int(player.get("player_stats").get("Headshots %"))
                    mvps = int(player.get("player_stats").get("MVPs"))
                    triple_kills = int(player.get("player_stats").get("Triple Kills"))
                    quadro_kills = int(player.get("player_stats").get("Quadro Kills"))
                    penta_kills = int(player.get("player_stats").get("Penta Kills"))
                    kd_ratio =  float(format(float(player.get("player_stats").get("K/D Ratio")), '.2f'))
                    kr_ratio =  float(format(float(player.get("player_stats").get("K/R Ratio")), '.2f'))
                    dpr_ratio = int(player.get("player_stats").get("Deaths")) / rounds
                    total_rounds =  rounds
                    match_length_seconds: match_length_seconds

                    PLAYER_STAT_VALUES = {
                        'kills': kills,
                        'assists': assists,
                        'deaths': deaths,
                        'headshots': headshots,
                        'headshot_percentage': headshot_percentage,
                        'mvps': mvps,
                        'triple_kills': triple_kills,
                        'quadro_kills': quadro_kills,
                        'penta_kills': penta_kills,
                        'kd_ratio': kd_ratio,
                        'kr_ratio': kr_ratio,
                        'dpr_ratio': dpr_ratio,
                        'total_rounds': total_rounds,
                        'match_length_seconds': match_length_seconds,
                        'kr_ratio_worst': kr_ratio,
                    }

                    args = [match_id, guild_id, player_guid, win, player_team_rank, player_team_first_half_score,
                            player_team_second_half_score, player_team_overtime_score, started_at, finished_at, added_timestamp,
                            kills, assists, deaths, headshots, headshot_percentage, mvps, triple_kills, quadro_kills,
                            penta_kills, kd_ratio, kr_ratio, dpr_ratio, total_rounds, match_length_seconds]
                    current_records = await get_records_by_guild(guild_id)
                    for record, stat in zip(current_records.values(), PLAYER_STAT_VALUES.values()):
                        record_item = record.get("record_item") # This is the item that comes from the DB
                        record_identifier = record.get("identifier")
                        record_condition = record.get("condition")
                        if record_item:
                            record_value = record_item[0][0]  # This is the actual record value (eq. most assists)
                            record_holder = record_item[0][1]  # This is the actual record value (eq. most assists)
                            player_stat = PLAYER_STAT_VALUES.get(record_identifier)
                            if (record_condition == '>' and player_stat > record_value) or ((record_condition == '<' and player_stat < record_value)):
                                log.info("record %s broken, previous record %s by %s" % (record_identifier, record_value, record_holder))
                                await faceit_db.add_record(args)
                                break # If only one record is broken, it is already enough for adding an item

                        else:
                            record_minimum_requirement = record.get("minimum_requirement")
                            if (record_condition == '>' and stat > record_minimum_requirement) or (record_condition == '<' and stat > record_minimum_requirement):
                                log.info("New record: %s, value %s" % (record_identifier, stat))
                                await faceit_db.add_record(args)
                                break # If only one record is broken, it is already enough for adding an item



async def get_player_rank_in_team(players_list, player_dict):
    return sorted(players_list, reverse=True, key=lambda x: int(x.get("player_stats").get("Kills"))).index(player_dict) + 1


async def get_server_rankings_per_guild():
    ranking = await faceit_db.get_toplist_per_guild_from_db()
    ranking_dict = {}
    for item in ranking:
        guild_id, nickname, elo, ranking = item
        if guild_id not in ranking_dict:
            ranking_dict.update({guild_id: [[nickname, elo, ranking]]})
        else:
            dict_item = ranking_dict.get(guild_id)
            dict_item.append([nickname, elo, ranking])
    return ranking_dict


async def fetch_players_batch(player_ids):
    responses = await pmap(fc.get_user_stats_from_api_by_id, player_ids)
    return dict(zip(player_ids, responses))


async def spam(client, faceit_nickname, spam_channel_id, current_elo, elo_before, current_skill,
                                 skill_before, custom_nickname, match_info_string, record_string):
    await asyncio.sleep(0.1)
    channel = discord.Object(id=spam_channel_id)
    message = None

    if skill_before < current_skill:
        msg = '**%s%s** gained **%s** elo and a new skill level! (Skill level %s -> %s, Elo now: %s)\n%s\n%s' % (
                                                        faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                        skill_before, current_skill, current_elo, match_info_string, record_string)
        util.threadsafe(client, client.send_message(channel, msg[:2000]))
        return
    elif skill_before > current_skill:
        msg = '**%s%s** lost **%s** elo and lost a skill level! (Skill level %s -> %s, Elo now: %s)\n%s\n%s' % (
                                                        faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                        skill_before, current_skill, current_elo, match_info_string, record_string)
        util.threadsafe(client, client.send_message(channel, msg[:2000]))
        return
    elif current_elo > elo_before:
        msg = '**%s%s** gained **%s** elo! (%s -> %s)\n%s' % (
            faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo,
            match_info_string)
        util.threadsafe(client, client.send_message(channel, msg[:2000]))
        return
    elif elo_before > current_elo:
        msg = '**%s%s** lost **%s** elo! (%s -> %s)\n%s' % (
            faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo,
            match_info_string)
        util.threadsafe(client, client.send_message(channel, msg[:2000]))
        return


# Combines match stats and match details (from two different api endpoints) to a dict
async def get_combined_match_data(matches):
    combined = {}
    for match in matches:
        match_id = match.get("match_id")
        match_details = await get_match_details(match.get("match_id"))
        if match_details.get("game") != 'csgo':
            log.info("Match is not csgo, skipping.. %s" % match_details) # Faceit api is so much fun that there aren't
            # just csgo matches in the csgo endpoints
            continue
        elif not match_details:
            log.info("Match details not available, skipping.. %s" % match_details)
            continue
        match_stats = await get_match_stats(match.get("match_id"))
        if not match_stats:
            log.info("Match stats not available, skipping.. %s" % match_details)
            continue
        combined.update({match_id: {
                                    'match_details': match_details,
                                    'match_stats': match_stats[0]
                                    }
                        })
    return combined


async def get_match_stats_string(player_guid, matches_dict):
    i = 1
    match_info_string = ""
    for match in matches_dict.values():
        match_details = match.get('match_details')
        match_stats = match.get('match_stats')
        score_string, stats_string = await get_info_strings(match_details, match_stats, player_guid)
        match_length_string = await get_match_length_string(match_details)
        match_info_string += "%s %s %s %s\n" % (
        ("**Match %s**" % i) if len(matches_dict) > 1 else "**Match**", score_string, stats_string, match_length_string)
        i += 1
        if i > 10:  # Only fetch a max of 10 matches
            break
    if not match_info_string:
        return match_info_string
    else:
        return "*" + match_info_string.rstrip("\n") + "*"


async def get_match_details(match_id):
    try:
        return await faceit_api.match(match_id)
    except NotFound as e:
        log.error(e)
        return None


async def get_info_strings(match_details, match_stats, player_guid):
    score_string = await get_score_string(match_stats)
    player_stats_string = await get_player_strings(match_stats, match_details, player_guid)
    return score_string, player_stats_string


async def get_match_stats(match_id):
    try:
        return await faceit_api.match_stats(match_id)
    except NotFound as e:
        log.error(e)


async def get_score_string(match_stats):
    if not match_stats.get("round_stats").get("Score"):
        log.error("SCORE MISSING ERROR: %s" % match_stats)
        return ""
    overtime_score = None
    map = match_stats.get("round_stats").get("Map")
    score = match_stats.get("round_stats").get("Score").replace(' / ', '-')
    first_half_score = "%s-%s" % (match_stats.get("teams")[0].get("team_stats").get("First Half Score"),
                                  match_stats.get("teams")[1].get("team_stats").get("First Half Score"))
    second_half_score = "%s-%s" % (match_stats.get("teams")[0].get("team_stats").get("Second Half Score"),
                                   match_stats.get("teams")[1].get("team_stats").get("Second Half Score"))
    total_rounds = int(match_stats.get("round_stats").get("Rounds"))
    if total_rounds > 30:
        overtime_score = "%s-%s" % (
            match_stats.get("teams")[0].get("team_stats").get("Overtime score"),
            match_stats.get("teams")[1].get("team_stats").get("Overtime score"))
    if overtime_score:
        score_string = ("**Map**: %s **score**: %s (%s, %s, %s)" % (
        map, score, first_half_score, second_half_score, overtime_score))
    else:
        score_string = ("**Map**: %s **score**: %s (%s, %s)" % (map, score, first_half_score, second_half_score))
    return score_string


async def get_player_strings(match_stats, match_details, player_guid):
    teams = match_stats.get("teams")
    for team in teams:
        for player in team.get("players"):
            if player.get('player_id') == player_guid:
                player_team = teams.pop(teams.index(team))
                enemy_team = teams[0]

                player_team_details = match_details.get("teams").get("faction1") if match_details.get("teams").get("faction1").get("faction_id") == player_team.get("team_id") else match_details.get("teams").get("faction2")
                enemy_team_details = match_details.get("teams").get("faction1") if match_details.get("teams").get("faction1").get("faction_id") == enemy_team.get("team_id") else match_details.get("teams").get("faction2")
                player_team_stats = player_team.get("players")
                enemy_team_stats = enemy_team.get("players")

                player_team = await merge_stats_and_details(player_team_details, player_team_stats)
                enemy_team = await merge_stats_and_details(enemy_team_details, enemy_team_stats)
                if not player_team or not enemy_team:
                    return ""

                player = [player_obj for player_obj in player_team if player_obj.guid == player.get("player_id")][0]

                highlight_string = await fh.get_highlights(player, match_stats, match_details, player_team, enemy_team)
                return "**Player stats:** #%s %s-%s-%s (%s kdr) %s" % (player.rank, player.kills, player.assists, player.deaths, player.kd_ratio, ("\n" + highlight_string if highlight_string else ''))
    return ""


    # Creates an object of every player and returns team's players sorted by kills (old api)
async def merge_stats_and_details_old_api(team_player_details, team_player_stats):
    merged = []
    for x in team_player_details.get("roster_v1"):
        for y in team_player_stats:
            if x.get("guid") == y.get("player_id"):
                player = create_player_obj_old_api(team_player_stats.index(y)+1, {**x, **y})
                merged.append(player)
    return sorted(merged, key=lambda x: x.rank)


# Creates an object of every player and returns team's players sorted by kills
async def merge_stats_and_details(team_player_details, team_player_stats):
    team_player_stats = sorted(team_player_stats, reverse=True, key=lambda x: int(x.get("player_stats").get("Kills")))
    if team_player_details.get("roster_v1"):
        return await merge_stats_and_details_old_api(team_player_details, team_player_stats)
    if team_player_details.get("roster"):
        merged = []
        for x in team_player_details.get("roster"):
            for y in team_player_stats:
                if x.get("player_id") == y.get("player_id"):
                    merged.append(create_player_obj(team_player_stats.index(y)+1, {**x, **y}))
        return sorted(merged, key=lambda x: x.rank)


async def get_match_length_string(match):

    async def get_length_string(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return '**Match length**: {:d}:{:02d}:{:02d}'.format(h, m, s)

    started_at = match.get("started_at")
    finished_at = match.get("finished_at")
    return await get_length_string(finished_at - started_at)


async def get_matches(player_guid, from_timestamp, to_timestamp=None):
    try:
        return await faceit_api.player_match_history(player_guid, from_timestamp, to_timestamp)
    except NotFound as e:
        log.error(e)
        return None


async def compare_toplists(client, old_toplist_dict):
    new_toplist_dict = await get_server_rankings_per_guild()
    log.info("Comparing toplists")
    for key in old_toplist_dict:
        spam_channel_id = await faceit_db.get_spam_channel_by_guild(key)
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


def create_player_obj(rank, player_dict):
    return PlayerStats \
            (
            player_dict.get("nickname"),
            player_dict.get("player_id"),
            player_dict.get("game_skill_level"),
            rank,
            int(player_dict.get("player_stats").get("Kills")),
            int(player_dict.get("player_stats").get("Assists")),
            int(player_dict.get("player_stats").get("Deaths")),
            int(player_dict.get("player_stats").get("Headshot")),
            int(player_dict.get("player_stats").get("Headshots %")),
            float(player_dict.get("player_stats").get("K/D Ratio")),
            float(player_dict.get("player_stats").get("K/R Ratio")),
            int(player_dict.get("player_stats").get("MVPs")),
            int(player_dict.get("player_stats").get("Penta Kills")),
            int(player_dict.get("player_stats").get("Quadro Kills")),
            int(player_dict.get("player_stats").get("Triple Kills")),
            int(player_dict.get("player_stats").get("Result"))
        )


def create_player_obj_old_api(rank, player_dict):
    return PlayerStats \
            (
            player_dict.get("nickname"),
            player_dict.get("player_id"),
            player_dict.get("csgo_skill_level"),
            rank,
            int(player_dict.get("player_stats").get("Kills")),
            int(player_dict.get("player_stats").get("Assists")),
            int(player_dict.get("player_stats").get("Deaths")),
            int(player_dict.get("player_stats").get("Headshot")),
            int(player_dict.get("player_stats").get("Headshots %")),
            float(player_dict.get("player_stats").get("K/D Ratio")),
            float(player_dict.get("player_stats").get("K/R Ratio")),
            int(player_dict.get("player_stats").get("MVPs")),
            int(player_dict.get("player_stats").get("Penta Kills")),
            int(player_dict.get("player_stats").get("Quadro Kills")),
            int(player_dict.get("player_stats").get("Triple Kills")),
            int(player_dict.get("player_stats").get("Result"))
        )

class PlayerStats:
    nickname = None
    guid = None
    faceit_level = None
    rank = None
    kills = None
    assists = None
    deaths = None
    headshots = None
    headshots_perc = None
    kd_ratio = None
    kr_ratio = None
    mvps = None
    result = None
    penta_kills = None
    quadro_kills = None
    triple_kills = None
    result = None

    def __init__(self, nickname, guid, faceit_level, rank, kills, assists, deaths, headshots, headshots_perc, kd_ratio,
                 kr_ratio, mvps, penta_kills, quadro_kills, triple_kills, result):
        self.nickname = nickname
        self.guid = guid
        self.faceit_level = faceit_level
        self.rank = rank
        self.kills = kills
        self.assists = assists
        self.deaths = deaths
        self.headshots = headshots
        self.headshots_perc = headshots_perc
        self.kd_ratio = kd_ratio
        self.kr_ratio = kr_ratio
        self.mvps = mvps
        self.result = result
        self.penta_kills = penta_kills
        self.quadro_kills = quadro_kills
        self.triple_kills = triple_kills
        self.result = result



# async def create_match_obj(match_details, match_stats):
#     return Match(
#         int(match_details.get("match_id")),
#         int(match_stats.get("game_id")),
#         int(match_stats.get("game_mode")),
#         int(match_stats.get("match_round")),
#         int(match_stats.get("played")),
#         int(match_details.get("competition_type")),
#         int(match_details.get("competition_name")),
#         int(match_details.get("teams")),
#         int(match_stats.get("teams")),
#         int(match_stats.get("round_stats")),
#         int(match_details.get("started_at")),
#         int(match_details.get("finished_at")),
#         int(match_details.get("finished_at")) - int(match_details.get("finished_at")) / int(
#             match_stats.get("round_stats").get("Rounds"))
#     )
#

# class Match:
#     match_id = None
#     game_id = None
#     game_mode = None
#     match_round = None
#     played = None
#     competition_type = None
#     competition_name = None
#     best_of = None
#     round_stats = {}
#     teams_1 = {}
#     teams_2 = {}
#     team_stats_sorted_by_rank = {}
#     started_at = None
#     finished_at = None
#     map_average_length = None
#
#     def __init__(self, match_id, game_id, game_mode, match_round, played, competition_type, competition_name, teams_1,
#                  teams_2, round_stats, started_at, finished_at, map_average_length):
#         self.match_id = match_id
#         self.game_id = game_id
#         self.game_mode = game_mode
#         self.match_round = match_round
#         self.played = played
#         self.competition_type = competition_type
#         self.competition_name = competition_name
#         self.teams_1 = teams_1
#         self.teams_2 = teams_2
#         self.round_stats = round_stats
#         self.started_at = started_at
#         self.finished_at = finished_at
#         self.map_average_length = map_average_length
#
# async def test(player_guid, timestamp):
#     print('time at start %s' % datetime.datetime.now())
#     matches = await get_matches(player_guid, timestamp)
#     print('time at matches %s' % datetime.datetime.now())
#     matches = await get_combined_match_data(matches)
#     await handle_records(player_guid, matches, "123123132")
#
#     print(await get_record_string("e6234673-9422-4517-a9f4-7722b57cfdf5", "123123132", matches))
#     # print(sorted(matches.values(), key=lambda x: x.get("match_details").get("started_at"))[0].get("match_details").get("started_at"))
#     # return
#     # #await handle_records(player_guid, matches)
#     # print('time at matches2 %s' % datetime.datetime.now())
#     # print(matches)
#     # if matches:
#     #     print('time at here3 %s' % datetime.datetime.now())
#     #     match_stats_string = await get_match_stats_string(player_guid, matches)
#     #     print('time at here4 %s' % datetime.datetime.now())
#     #     print(match_stats_string)
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test("e6234673-9422-4517-a9f4-7722b57cfdf5",1560377896))