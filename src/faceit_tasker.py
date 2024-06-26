
import faceit_db_functions as faceit_db
import asyncio
import util
import logger
from faceit_api import UnknownError
from time_util import to_utc
from util import pmap
import faceit_highlights as fh
import faceit_common as fc
import faceit_records as fr
import faceit_api
import copy
import traceback

NOT_A_PM_COMMAND_ERROR = "This command doesn't work in private chat."

log = logger.get("FACEIT")


async def elo_notifier_task(client):
    try:
        await check_faceit_elo(client)
    except UnknownError as e:
        if 500 <= e.response.status <= 599:
            # Faceit API is broken and  there's probably very little we can
            # do so no reason to spam errors channel
            log.warning("Failed to check faceit stats\n" + traceback.format_exc())
        else:
            raise e


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

        # Skip check if faceit api call failed for the player
        if player_guid not in api_responses: continue
        current_elo, skill_level, csgo_name, ranking, last_played = api_responses[player_guid]

        player_db_stats = await faceit_db.get_faceit_stats_of_player(player_guid)
        if player_db_stats:
            await fc.do_nick_change_check(player_guid, csgo_name, player_database_nick)
            if not current_elo or not ranking or not player_db_stats['faceit_ranking'] or not player_db_stats[
                'faceit_ranking']:  # Currently, only EU ranking is supported
                continue
            if current_elo != player_db_stats['faceit_elo']:
                await faceit_db.insert_data_to_player_stats_table(player_guid, current_elo, skill_level,
                                                                  ranking)
                player_all_time_stats = await faceit_api.player_stats(player_guid)
                matches = await faceit_api.player_match_history(player_guid, int(to_utc(player_db_stats['changed']).timestamp()))
                matches = await fc.get_combined_match_data(matches)
                for channel_id, custom_nickname in await faceit_db.channels_to_notify_for_user(player_guid): #todo fix this, doesn't have to be done again for each server
                    channel = await client.fetch_channel(int(channel_id))
                    log.info("Notifying channel %s", channel.id)
                    if matches:
                        match_stats_string = await get_match_stats_string(player_all_time_stats, copy.deepcopy(matches))
                        guild_id = channel.guild.id
                        await fr.handle_records(player_guid, copy.deepcopy(matches), guild_id)
                        records_string = await fr.get_record_string(player_guid, guild_id, copy.deepcopy(matches))
                    else:
                        log.info("No matches found for user %s" % player_guid)
                        match_stats_string = ''
                        records_string = ''
                    await spam(client, record['faceit_nickname'], channel_id,
                                                 current_elo, player_db_stats['faceit_elo'], skill_level,
                                                 player_db_stats['faceit_skill'], (
                                                     ' "' + custom_nickname + '"' if custom_nickname else ''),
                                                 match_stats_string, records_string)

        else:
            if not current_elo or not ranking:  # Currently, only EU ranking is supported
                continue
            await faceit_db.insert_data_to_player_stats_table(player_guid, current_elo, skill_level,
                                                              ranking)
    await compare_toplists(client, old_toplist_dict)
    log.info('Faceit stats checked')


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
    def is_error_response(response_tuple):
        return all(x is None for x in response_tuple)

    responses = await pmap(fc.get_user_stats_from_api_by_id, player_ids)

    result = dict()
    for player_id, response in zip(player_ids, responses):
        if not is_error_response(response):
            result[player_id] = response
    return result

async def spam(client, faceit_nickname, spam_channel_id, current_elo, elo_before, current_skill,
                                 skill_before, custom_nickname, match_info_string, record_string):
    await asyncio.sleep(0.1)
    channel = await client.fetch_channel(int(spam_channel_id))
    message = None

    if skill_before < current_skill:
        msg = '**%s%s** gained **%s** elo and a new skill level! (Skill level %s -> %s, Elo now: %s)\n%s\n%s' % (
                                                        faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                        skill_before, current_skill, current_elo, match_info_string, record_string)
        await channel.send(msg[:2000])
        return
    elif skill_before > current_skill:
        msg = '**%s%s** lost **%s** elo and lost a skill level! (Skill level %s -> %s, Elo now: %s)\n%s\n%s' % (
                                                        faceit_nickname, custom_nickname, int(current_elo - elo_before),
                                                        skill_before, current_skill, current_elo, match_info_string, record_string)
        await channel.send(msg[:2000])
        return
    elif current_elo > elo_before:
        msg = '**%s%s** gained **%s** elo! (%s -> %s)\n%s\n%s' % (
            faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo,
            match_info_string, record_string)
        await channel.send(msg[:2000])
        return
    elif elo_before > current_elo:
        msg = '**%s%s** lost **%s** elo! (%s -> %s)\n%s\n%s' % (
            faceit_nickname, custom_nickname, int(current_elo - elo_before), elo_before, current_elo,
            match_info_string, record_string)
        await channel.send(msg[:2000])
        return


async def get_match_stats_string(player_all_time_stats, matches_dict) -> str:
    i = 1
    player_guid = player_all_time_stats.get('player_id')
    match_number = int(player_all_time_stats.get('lifetime').get('Matches', 0)) #todo what if no matches yet?
    match_info_string = ""
    for match in matches_dict.values():
        match_details = match.get('match_details')
        match_stats = match.get('match_stats')
        score_string, stats_string = await get_info_strings(match_details, match_stats, player_guid)
        match_length_string = await get_match_length_string(match_details)
        match_info_string += "%s %s %s %s\n" % (
        ("**Match (#%s) %s of %s**" % (match_number + i, i, len(matches_dict))) if has_multiple_matches(matches_dict) else "**Match (#%s)**" % (match_number+1), score_string, match_length_string, stats_string)
        i += 1
        if i > 10:  # Only fetch a max of 10 matches
            break
    if not match_info_string:
        return match_info_string
    else:
        return "*" + match_info_string.rstrip("\n") + "*"


def has_multiple_matches(matches_dict) -> bool:
    return len(matches_dict) > 1


async def get_info_strings(match_details, match_stats, player_guid):
    score_string = await get_score_string(match_stats)
    player_stats_string = await get_player_strings(match_stats, match_details, player_guid)
    return score_string, player_stats_string


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
                return "**Player stats:** #%s %s-%s-%s (%s kdr)%s" % (player.rank, player.kills, player.assists, player.deaths, player.kd_ratio, ("\n" + highlight_string if highlight_string else ''))
    return "Player ragequit from the match!" # Player is not in either team, which means they have left the match

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
        channel = await client.fetch_channel(int(spam_channel_id))
        await channel.send(msg)
        await asyncio.sleep(.25)
    log.info("Rank changes checked")


def create_player_obj(rank, player_dict):
    return PlayerStats \
            (
            player_dict.get("nickname"),
            player_dict.get("player_id"),
            player_dict.get("game_skill_level"),
            rank,
            int(player_dict.get("player_stats").get("Kills", 0)),
            int(player_dict.get("player_stats").get("Assists", 0)),
            int(player_dict.get("player_stats").get("Deaths", 0)),
            int(player_dict.get("player_stats").get("Headshots", 0)),
            int(player_dict.get("player_stats").get("Headshots %", 0)),
            float(player_dict.get("player_stats").get("K/D Ratio", 0)),
            float(player_dict.get("player_stats").get("K/R Ratio", 0)),
            int(player_dict.get("player_stats").get("MVPs", 0)),
            int(player_dict.get("player_stats").get("Penta Kills", 0)),
            int(player_dict.get("player_stats").get("Quadro Kills", 0)),
            int(player_dict.get("player_stats").get("Triple Kills", 0)),
            int(player_dict.get("player_stats").get("Result"))
        )


def create_player_obj_old_api(rank, player_dict):
    return PlayerStats \
            (
            player_dict.get("nickname"),
            player_dict.get("player_id"),
            player_dict.get("csgo_skill_level"),
            rank,
            int(player_dict.get("player_stats").get("Kills", 0)),
            int(player_dict.get("player_stats").get("Assists", 0)),
            int(player_dict.get("player_stats").get("Deaths", 0)),
            int(player_dict.get("player_stats").get("Headshot", 0)),
            int(player_dict.get("player_stats").get("Headshots %", 0)),
            float(player_dict.get("player_stats").get("K/D Ratio", 0)),
            float(player_dict.get("player_stats").get("K/R Ratio", 0)),
            int(player_dict.get("player_stats").get("MVPs", 0)),
            int(player_dict.get("player_stats").get("Penta Kills", 0)),
            int(player_dict.get("player_stats").get("Quadro Kills", 0)),
            int(player_dict.get("player_stats").get("Triple Kills", 0)),
            int(player_dict.get("player_stats").get("Result", 0))
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
