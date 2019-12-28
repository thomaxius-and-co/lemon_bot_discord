import random
import logger
import json

log = logger.get("FACEIT_HIGHLIGHTS")

async def get_highlights(player, match_stats, match_details, player_team, enemy_team):
    match_length = int(match_details.get("finished_at")) - int(match_details.get("started_at"))
    match_length = match_length / int(
        match_stats.get("best_of"))  # Best of 3 matches are count as one match length..
    rounds = int(match_stats.get("round_stats").get("Rounds"))

    player_team_total_kills = await get_team_total_kills(player_team)
    enemy_team_total_kills = await get_team_total_kills(enemy_team)
    match_total_kills = player_team_total_kills + enemy_team_total_kills

    player_team_total_deaths = await get_team_total_deaths(player_team)
    enemy_team_total_deaths = await get_team_total_deaths(enemy_team)
    match_total_deaths = player_team_total_deaths + enemy_team_total_deaths

    highlights = {
        'PENTA_KILLS': {
                        'condition': (player.penta_kills >= 1),
                        'description': "**The acer**: **%s** penta kill(s)" % (player.penta_kills),
                        'priority': 100,
                        'priority_multiplier': player.penta_kills
                        },
        'QUADRO_KILLS': {
                        'condition': (player.quadro_kills >= 1),
                        'description': "**Idiot, why no give ace?**: **%s** quadro kill(s)" % (player.quadro_kills),
                        'priority': 60,
                        'priority_multiplier': player.quadro_kills
                        },
        'TRIPLE_KILLS': {
                        'condition': (player.triple_kills >= 2),
                        'description': "**The hat tricker**: **%s** triple kill(s)" % (player.triple_kills),
                        'priority': 50,
                        'priority_multiplier': player.triple_kills
                        },
        'ASSIST_KING': {
                        'condition': (player.assists > player.kills),
                        'description': "**Helping hand**: More assists (%s) than kills (%s)" % (player.assists, player.kills),
                        'priority': 70,
                        'priority_multiplier': rounds / 7
                        },
        'MANY_KILLS_AND_LOSE': {
                        'condition': ((player.kr_ratio >= 0.9) or (player.kd_ratio >= 1.4)) and (player.result == 0) and (rounds > 25),
                        'description': "**All that for nothing**: %s kills (%s kdr/%s kpr) and still lost the match" % (player.kills, player.kd_ratio, player.kr_ratio),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio if player.kd_ratio >= 1.4 else (1 + player.kr_ratio)
                        },
        'HEADSHOTS_KING': {
                        'condition': (player.headshots_perc >= 65) and rounds >= 20,
                        'description': "**Zombie killer**: **%s** headshot percentage (%s headshots out of %s kills)" % (player.headshots_perc, player.headshots, player.kills),
                        'priority': 50,
                        'priority_multiplier': rounds / 15
                        },
        'MANY_KILLS_NO_MVPS': {
                        'condition': ((player.kr_ratio >= 0.9) or (player.kd_ratio >= 1.7)) and (rounds > 20) and (player.mvps <= 2),
                        'description': "**Quantity not quality**: {0} kills but only {1} mvps ({2} kills per round)".format(player.kills, player.mvps,  player.kr_ratio),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'BAD_STATS_STILL_WIN': {
                        'condition': (player.kd_ratio <= 0.6) and (player.result == 1),
                        'description': "**Steven Bradbury**: Won the match even though they had %s-%s-%s" % (player.kills, player.assists, player.deaths),
                        'priority': 90,
                        'priority_multiplier': 1 + player.deaths / 10
                        },
        'DIED_EVERY_ROUND': {
                        'condition': (player.deaths == rounds),
                        'description': "**The kamikazer**:  Died every round (%s times)" % (player.deaths),
                        'priority': 80,
                        'priority_multiplier': rounds / 10
                        },
        'DIED_OFTEN': {
                        'condition': ((player.deaths / rounds) * 100) >= 90 and (player.deaths != rounds),
                        'description': "**Save no weapons**: Died almost every round (%s times out of %s rounds)" % (player.deaths, rounds),
                        'priority': 80,
                        'priority_multiplier': rounds / 10
        },
        'TOP_FRAGGER_LOWEST_LEVEL_IN_TEAM': {
                        'condition': await is_team_topfragger_but_lowest_level(player, player_team),
                        'description': "**The Dark Horse (team)**: Top fragger even though was the lowest level in the team",
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'BOTTOM_FRAGGER_HIGHEST_LEVEL_IN_TEAM': {
                        'condition': await is_team_bottomfragger_but_highest_level(player, player_team),
                        'description': "**Overrated (team)**: Bottom fragger even though was the highest level in the team",
                        'priority': 70,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'TOP_FRAGGER_LOWEST_LEVEL_IN_MATCH': {
                        'condition': await is_match_topfragger_but_lowest_level(player, player_team, enemy_team),
                        'description': "**The Dark Horse (match)**: Top fragger even though was the lowest level (%s) in the match" % (player.faceit_level),
                        'priority': 90,
                        'priority_multiplier': player.kd_ratio
                        },
        'BOTTOM_FRAGGER_HIGHEST_LEVEL_IN_MATCH': {
                        'condition': await is_match_bottomfragger_but_highest_level(player, player_team, enemy_team),
                        'description': "**Overrated (match)**: Bottom fragger even though was the highest level (%s) in the match" % (player.faceit_level),
                        'priority': 90,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'MATCH_TOP_FRAGGER': {
                        'condition': await is_match_topfragger(player, player_team, enemy_team),
                        'description': "**Windy at the top**: Top fragger of the match with %s kills" % (player.kills),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'MATCH_BOTTOM_FRAGGER': {
                        'condition': await is_match_bottomfragger(player, player_team, enemy_team),
                        'description': "**Who needs frags anyway**: Bottom fragger of the match",
                        'priority': 70,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'MATCH_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / match_total_kills) * 100) >= 15,
                        'description': "**Leave nothing for friends**: Had **{0:.3g}**% of the match total kills ({1})".format(((player.kills / match_total_kills) * 100), match_total_kills),
                        'priority': 60,
                        'priority_multiplier': 1 + (player.kills / match_total_kills)
                        },
        'TEAM_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / player_team_total_kills) * 100) >= 30,
                        'description': "**Get carried**: **{0:.3g}**% of team total kills ({1})".format(((player.kills / player_team_total_kills) * 100), player_team_total_kills),
                        'priority': 40,
                        'priority_multiplier': 1.2 + (player.kills / enemy_team_total_kills)
                        },
        'ENEMY_TEAM_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / enemy_team_total_kills) * 100) >= 30,
                        'description': "**One man army**: **{0:.3g}**% of enemy team's total kills ({1})".format(((player.kills / enemy_team_total_kills) * 100),
                                                                                                                         enemy_team_total_kills),
                        'priority': 30,
                        'priority_multiplier': 1.2 + (player.kills / enemy_team_total_kills)
                        },
        'MATCH_TOP_ASSISTER': {
                        'condition': await is_match_top_assister(player, player_team, enemy_team),
                        'description': "**Helping hand (match)**: Most assists (%s) in the match" % (player.assists),
                        'priority': 70,
                        'priority_multiplier': 1 + (player.assists / rounds)
                        },
        'TEAM_TOP_ASSISTER': {
                        'condition': await is_team_top_assister(player, player_team) and not await is_match_top_assister(player, player_team, enemy_team), #todo fix..
                        'description': "**Helping hand (team)**: Team top assister (%s assists)" % (player.assists),
                        'priority': 70,
                        'priority_multiplier': 1 + (player.assists / rounds)
                        },
        'LONG_MATCH': {
                        'condition': ((match_length / rounds) >= 115),
                        'description': "**Going the distance**: rounds had an average length of **{0:.3g}** minutes".format(
                           (match_length / 60) / rounds),
                        'priority': 50,
                        'priority_multiplier': ((match_length / rounds) / 75)
                        },
        'MANY_KILLS_MULTI_KILLS': {
                        'condition': await has_many_kills_multi_kills(player),
                        'description': "**I only do 'em if I can do 'em all**: **{0:.3g}**% of kills consist(ed) of either triple, quad or penta kills ({1}t-{2}q-{3}p)".format(
                            ((((player.penta_kills * 5) + (player.quadro_kills * 4) + (player.triple_kills * 3)) / player.kills) * 100),  player.triple_kills, player.quadro_kills, player.penta_kills),
                        'priority': 50,
                        'priority_multiplier': rounds / 10
                         },
        'BIG_MVP_PERCENTAGE': {
                        'condition': ((player.mvps / rounds) * 100) >= 30,
                        'description': "**Only actions that count**: **{0}** mvp's (**{1:.3g}**% out of {2} rounds)".format(
                            player.mvps, ((player.mvps / rounds) * 100), rounds),
                        'priority': 90,
                        'priority_multiplier': rounds / 10
                        },
        'BAD_HEADSHOT_RATE': {
                        'condition': (player.headshots_perc <= 20) and (player.kills >= 20),
                        'description': "**Quantity, not quality**: Headshot percentage of only **{0:.3g}**% ({1} of {2} kills)".format(
                            player.headshots_perc, player.headshots, player.kills),
                        'priority': 90,
                        'priority_multiplier': player.kills / 10
        },
        'HIGH_KR_RATIO': {
                        'condition': (player.kr_ratio >= 1.2) and (rounds >= 15),
                        'description': "**Must I do all the work**: Average of **{0}** kills per round".format(
                            player.kr_ratio),
                        'priority': 50,
                        'priority_multiplier': player.kr_ratio
        },
        'LOW_KR_RATIO_LOW_DPR_RATIO': {
                        'condition': (player.kr_ratio <= 0.5) and (rounds >= 15) and (player.kd_ratio >= 0.9),
                        'description': "**Sorry I was asleep**: Average of only **{0}** kills per round and only {1} deaths.".format(
                            player.kr_ratio, player.deaths),
                        'priority': 50,
                        'priority_multiplier': player.kr_ratio * 10
        },
        'DIED_THE_MOST': {
                        'condition': await died_the_most(player, player_team, enemy_team),
                        'description': "**Sean Bean**: Died the most times in the match ({0} times)".format(
                            player.deaths),
                        'priority': 50,
                        'priority_multiplier': player.deaths / 10
        },
        'TOP_FRAGGER_FEW_KILLS': {
                        'condition': player.rank == 1 and player.kr_ratio <= 0.7 and rounds >= 15,
                        'description': "**Minimum effort, best effort**: Top fragger of the team with just **{0}** kills.".format(
                            player.kills),
                        'priority': 70,
                        'priority_multiplier': rounds / 10
        },
        'BOTTOM_FRAGGER_GOOD_KD': {
                        'condition': player.rank == 5 and player.kd_ratio >= 1.7 and rounds >= 10,
                        'description': "**Sweating for nothing**: Bottom fragger of the team even though had a kd ratio of **{0}**.".format(
                            player.kd_ratio),
                        'priority': 100,
                        'priority_multiplier': player.kd_ratio
        },
        'MATCH_DIED_BIG_AMOUNT': {
                        'condition': ((player.deaths / match_total_deaths) * 100) >= 15,
                        'description': "**Human shield (match)**: **{0:.3g}%** of the match's total deaths ({1}).".format(
                            (player.deaths / match_total_deaths) * 100, player.deaths),
                        'priority': 80,
                        'priority_multiplier': player.deaths / 10
        },
        'TEAM_DIED_BIG_AMOUNT': {
                        'condition': ((player.deaths / player_team_total_deaths) * 100) >= 30,
                        'description': "**Human shield (team)**: **{0:.3g}%** of team's total deaths ({1}).".format(
                            (player.deaths / player_team_total_deaths) * 100, player.deaths),
                        'priority': 80,
                        'priority_multiplier': player.deaths / 10
        },
        'ENEMY_BOTTOM_FRAGGER_TWICE_AS_GOOD': {
                        'condition': await enemy_bottom_fragger_twice_as_good(player, enemy_team),
                        'description': "**Let's not talk about this**: Enemy team's bottom fragger had **{0:.3g}%** times more kills ({1}) than {2}.".format(
                            (await get_bottom_fragger(enemy_team)).kills / player.kills, (await get_bottom_fragger(enemy_team)).kills, player.nickname),
                        'priority': 180,
                        'priority_multiplier': player.deaths / 10
        },
    }

    base_string = "**Player highlight(s)**:\n"
    highlight_string = base_string

    occured_highlights = []
    occured_highlights_priorities = []

    for x in highlights:
        condition, description, priority, priority_multiplier = highlights.get(x).values()
        if condition:
            priority *= priority_multiplier
            occured_highlights.append(x)
            occured_highlights_priorities.append(priority)

    if len(occured_highlights) == 0:
        return ""

    while len(occured_highlights) >= 1:
        chosen_highlight = random.choices(occured_highlights, occured_highlights_priorities)[0]
        chosen_highlight_description = highlights.get(chosen_highlight).get("description")
        del occured_highlights_priorities[occured_highlights.index(chosen_highlight)]
        occured_highlights.remove(chosen_highlight)
        highlight_string += "     - " + chosen_highlight_description + "\n"
    return highlight_string

async def players_sorted_by_kills(players_list):
    return sorted(players_list, reverse=True, key=lambda x: int(x.get("player_stats").get("Kills")))


async def get_team_details(team):
    if team.get("faction1").get("roster_v1"):
        return team.get("faction1").get("roster_v1") if team.get("faction1").get("faction_id") == team.get("team_id") else team.get("faction2").get("roster_v1")
    elif team.get("faction1").get("roster"):
        return team.get("faction1").get("roster_v1") if team.get("faction1").get("faction_id") == team.get("team_id") else team.get("faction2").get("roster_v1")


async def is_team_topfragger_but_lowest_level(player, player_team):
    all_levels_are_equal = all(x.faceit_level==player_team[0].faceit_level for x in player_team)
    if all_levels_are_equal:
        return False
    players = sorted(player_team, reverse=True, key=lambda x: x.faceit_level)
    return (player.rank == 1) and (players[-1].guid == player.guid)


async def is_team_bottomfragger_but_highest_level(player, player_team):
    all_levels_are_equal = all(x.faceit_level==player_team[0].faceit_level for x in player_team) #todo make a global function out of this
    if all_levels_are_equal:
        return False
    players = sorted(player_team, reverse=True, key=lambda x: int(x.faceit_level))
    if players[-1].faceit_level == players[-2].faceit_level: # if last two players have same level
        return False
    return (player.rank == 5) and (players[0].guid == player.guid)


async def is_match_topfragger_but_lowest_level(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    all_levels_are_equal = all(x.faceit_level==match_players[0].faceit_level for x in match_players)
    if all_levels_are_equal:
        return False
    match_players_by_level = sorted(match_players, reverse=True, key=lambda x: x.faceit_level)
    match_players_by_kills = sorted(match_players, reverse=True, key=lambda x: x.kills)
    if match_players_by_kills[0].faceit_level == match_players_by_kills[1].faceit_level: # Two topfraggers have the same level
        return False
    return (match_players_by_level[-1].guid == player.guid) and (match_players_by_kills[0].guid == player.guid)


async def is_match_bottomfragger_but_highest_level(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    all_levels_are_equal = all(x.faceit_level==match_players[0].faceit_level for x in match_players)
    if all_levels_are_equal:
        return False
    match_players_by_level = sorted(match_players, reverse=True, key=lambda x: x.faceit_level)
    match_players_by_kills = sorted(match_players, reverse=True, key=lambda x: x.kills)
    if match_players_by_kills[-1].faceit_level == match_players_by_kills[-2].faceit_level: # Two bottomfraggers have the same level
        return False
    return (match_players_by_level[0].guid == player.guid) and (match_players_by_kills[-1].guid == player.guid)


async def is_match_topfragger(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    match_players_by_kills = sorted(match_players, reverse=True, key=lambda x: x.kills)
    return match_players_by_kills[0].guid == player.guid


async def is_match_bottomfragger(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    match_players_by_kills = sorted(match_players, reverse=True, key=lambda x: x.kills)
    return match_players_by_kills[-1].guid == player.guid


async def is_match_top_assister(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    match_players_by_assists = sorted(match_players, reverse=True, key=lambda x: x.assists)
    return match_players_by_assists[0].guid == player.guid


async def get_team_total_kills(team):
    return sum([player.kills for player in team])

async def get_team_total_deaths(team):
    return sum([player.deaths for player in team])

async def has_many_kills_multi_kills(player):
    return ((((player.penta_kills * 5) + (player.quadro_kills * 4) + (player.triple_kills * 3)) / player.kills ) * 100) >= 50

async def died_the_most(player, player_team, enemy_team):
    match_players = player_team + enemy_team
    match_players_by_deaths = sorted(match_players, reverse=True, key=lambda x: x.deaths)
    return match_players_by_deaths[0].guid == player.guid


async def is_team_top_assister(player, player_team):
    team_players_by_assists = sorted(player_team, reverse=True, key=lambda x: x.assists)
    return team_players_by_assists[0].guid == player.guid

async def enemy_bottom_fragger_twice_as_good(player, enemy_team):
    enemy_bottom_fragger = await get_bottom_fragger(enemy_team)
    return enemy_bottom_fragger.kills >= (player.kills * 2)

async def get_bottom_fragger(team):
    return [player for player in team if player.rank == 5][0]