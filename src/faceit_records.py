import datetime
import logger
import faceit_db_functions as faceit_db
from datetime import datetime

log = logger.get("FACEIT_RECORDS")

async def get_records_by_guild(guild_id):
    records = {
        'MOST_KILLS': {
            'record_title': 'Most kills in a match',
            'record_item': await faceit_db.top_kills(guild_id, minimum_requirement=20),
            'condition': '>',
            'minimum_requirement': 20,
            'identifier': 'kills',
            'function': None
        },
        'MOST_ASSISTS': {
            'record_title': 'Most assists in a match',
            'record_item': await faceit_db.top_assists(guild_id, minimum_requirement=5),
            'condition': '>',
            'minimum_requirement': 5,
            'identifier': 'assists',
            'function': None
        },
        'MOST_DEATHS': {
            'record_title': 'Most deaths in a match',
            'record_item': await faceit_db.top_deaths(guild_id, minimum_requirement=20),
            'condition': '>',
            'minimum_requirement': 20,
            'identifier': 'deaths',
            'function': None
        },
        'MOST_HEADSHOTS': {
            'record_title': 'Most headshots in a match',
            'record_item': await faceit_db.top_headshots(guild_id, minimum_requirement=10),
            'condition': '>',
            'minimum_requirement': 10,
            'identifier': 'headshots',
            'function': None
        },
        'BIGGEST_HEADSHOT_PERCENTAGE': {
            'record_title': 'Biggest headshot percentage',
            'record_item': await faceit_db.top_headshot_percentage(guild_id, minimum_requirement=50),
            'condition': '>',
            'minimum_requirement': 50,
            'identifier': 'headshot_percentage',
            'function': None
        },
        'MOST_MVPS': {
            'record_title': 'Most mvps in a match',
            'record_item': await faceit_db.top_mvps(guild_id, minimum_requirement=5),
            'condition': '>',
            'minimum_requirement': 5,
            'identifier': 'mvps',
            'function': None
        },
        'MOST_TRIPLE_KILLS': {
            'record_title': 'Most triple kills in a match',
            'record_item': await faceit_db.top_triple_kills(guild_id, minimum_requirement=3),
            'condition': '>',
            'minimum_requirement': 3,
            'identifier': 'triple_kills',
            'function': None
        },
        'MOST_QUADRO_KILLS': {
            'record_title': 'Most quadro kills in a match',
            'record_item': await faceit_db.top_quadro_kills(guild_id, minimum_requirement=1),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'quadro_kills',
            'function': None
        },
        'MOST_PENTA_KILLS': {
            'record_title': 'Most penta kills in a match',
            'record_item': await faceit_db.top_penta_kills(guild_id, minimum_requirement=0),
            'condition': '>',
            'minimum_requirement': 0,
            'identifier': 'penta_kills',
            'function': None
        },
        'BIGGEST_KD_RATIO': {
            'record_title': 'Biggest kd ratio in a match',
            'record_item': await faceit_db.top_kdr(guild_id, minimum_requirement=1),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'kd_ratio',
            'function': None
        },
        'BIGGEST_KR_RATIO': {
            'record_title': 'Biggest kills per round ratio in a match',
            'record_item': await faceit_db.top_kpr(guild_id, minimum_requirement=1),
            'condition': '>',
            'minimum_requirement': 1,
            'identifier': 'kr_ratio',
            'function': None
        },
        'BIGGEST_DPR_RATIO': {
            'record_title': 'Most deaths per round in a match',
            'record_item': await faceit_db.top_dpr(guild_id, minimum_requirement=0.5),
            'condition': '>',
            'minimum_requirement': 0.5,
            'identifier': 'dpr_ratio',
            'function': None
        },
        'LONGEST_MATCH_ROUNDS': {
            'record_title': 'Longest match by rounds',
            'record_item': await faceit_db.match_most_rounds(guild_id, minimum_requirement=30),
            'condition': '>',
            'minimum_requirement': 30,
            'identifier': 'total_rounds',
            'function': None
        },
        'LONGEST_MATCH_SECONDS': {
            'record_title': 'Longest match by time',
            'record_item': await faceit_db.longest_match(guild_id, minimum_requirement=3000),
            'condition': '>',
            'minimum_requirement': 3000,
            'identifier': 'match_length_seconds',
            'function': get_length_string
        },
        'WORST_KD_RATIO': {
            'record_title': 'Worst kd ratio in a match',
            'record_item': await faceit_db.worst_kd_ratio(guild_id, minimum_requirement=0.5),
            'minimum_requirement': 0.5,
            'condition': '<',
            'identifier': 'kr_ratio_worst',
            'function': None
        },
    }
    return records


async def get_length_string(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:d}:{:02d}:{:02d}'.format(h, m, s)

async def get_record_string(player_guid, guild_id, matches):
    matches_sorted_by_time = sorted(matches.values(), reverse=True, key=lambda x: int(x.get("match_details").get("started_at")))
    earliest_match_timestamp = int(matches_sorted_by_time[-1].get("match_details").get("started_at"))
    current_records = await get_records_by_guild(guild_id)
    record_string = ""
    for record in current_records.values():
        record_item = record.get("record_item") # This is the item that comes from the DB
        if record_item:
            record_value = record_item[0][0]
            record_holder_guid = record_item[0]['faceit_guid']
            record_holder_name = record_item[0]['faceit_nickname']
            record_match_finished_at = record_item[0]['finished_at']
            if len(record_item) > 1:
                previous_record_value = record_item[1][0]
                if previous_record_value == record_value:
                    continue # Don't spam if record is same as before
                previous_record_holder_name = record_item[1]['faceit_nickname']
                previous_record_string = "(previous record: **%s** by **%s**)" % (previous_record_value, previous_record_holder_name)
            else:
                previous_record_string = ""
            record_title = record.get("record_title")
            if player_guid == record_holder_guid and record_match_finished_at >= earliest_match_timestamp:
                if record_string:
                    record_string += "**%s** (%s) %s\n" % (record_title, record_value, previous_record_string)
                else:
                    record_string = "**%s** broke the following records: **%s** (%s) %s\n" % (record_holder_name, record_title, record_value, previous_record_string)


    return record_string

async def get_player_rank_in_team(players_list, player_dict):
    return sorted(players_list, reverse=True, key=lambda x: int(x.get("player_stats").get("Kills"))).index(player_dict) + 1


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
                    kd_ratio = round(float(player.get("player_stats").get("K/D Ratio")),2)
                    kr_ratio = round(float(player.get("player_stats").get("K/R Ratio")),2)
                    dpr_ratio = round((int(player.get("player_stats").get("Deaths")) / rounds),2)
                    total_rounds = rounds
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
                                log.info("New record: %s, value %s made by %s" % (record_identifier, stat, player_guid))
                                await faceit_db.add_record(args)
                                break # If only one record is broken, it is already enough for adding an item