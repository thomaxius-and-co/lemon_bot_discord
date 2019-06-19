import random


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
                        'description': "**%s** had **%s** penta kill(s)" % (player.nickname, player.penta_kills),
                        'priority': 100,
                        'priority_multiplier': player.penta_kills
                        },
        'QUADRO_KILLS': {
                        'condition': (player.quadro_kills >= 1),
                        'description': "**%s** had **%s** quadro kill(s)" % (player.nickname, player.quadro_kills),
                        'priority': 60,
                        'priority_multiplier': player.quadro_kills
                        },
        'TRIPLE_KILLS': {
                        'condition': (player.triple_kills >= 2),
                        'description': "**%s** had **%s** triple kill(s)" % (player.nickname, player.triple_kills),
                        'priority': 50,
                        'priority_multiplier': player.triple_kills
                        },
        'ASSIST_KING': {
                        'condition': (player.assists > player.kills),
                        'description': "**%s** had more assists (%s) than kills (%s)" % (player.nickname, player.assists, player.kills),
                        'priority': 70,
                        'priority_multiplier': rounds / 7
                        },
        'MANY_KILLS_AND_LOSE': {
                        'condition': ((player.kr_ratio >= 0.9) or (player.kd_ratio >= 1.4)) and (player.result == 0) and (rounds > 25),
                        'description': "**%s** had %s kills (%s kdr/%s kpr) and still lost the match" % (player.nickname, player.kills, player.kd_ratio, player.kr_ratio),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio if player.kd_ratio >= 1.4 else (1 + player.kr_ratio)
                        },
        'HEADSHOTS_KING': {
                        'condition': (player.headshots_perc >= 65) and rounds >= 20,
                        'description': "**%s** had **%s** headshot percentage (%s headshots out of %s kills)" % (player.nickname, player.headshots_perc, player.headshots, player.kills),
                        'priority': 50,
                        'priority_multiplier': rounds / 15
                        },
        'MANY_KILLS_NO_MVPS': {
                        'condition': ((player.kr_ratio >= 0.9) or (player.kd_ratio >= 1.7)) and (rounds > 20) and (player.mvps <= 2),
                        'description': " **%s** had %s mvps but %s kills (%s per round)" % (player.nickname, player.mvps, player.kills, player.kr_ratio),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'BAD_STATS_STILL_WIN': {
                        'condition': (player.kd_ratio <= 0.6) and (player.result == 1),
                        'description': " **%s** won the match even though he was %s-%s-%s" % (player.nickname, player.kills, player.assists, player.deaths),
                        'priority': 90,
                        'priority_multiplier': 1 + player.deaths / 10
                        },
        'DIED_EVERY_ROUND': {
                        'condition': (player.deaths == rounds),
                        'description': " **%s** died every round (%s times)" % (player.nickname, player.deaths),
                        'priority': 80,
                        'priority_multiplier': rounds / 10
                        },
        'DIED_OFTEN': {
                        'condition': ((player.deaths / rounds) * 100) >= 90 and (player.deaths != rounds), # Don't do this highlight if DIED_EVERY_ROUND highlight is chosen todo: fix this
                        'description': " **%s** died almost every round (%s times out of %s rounds)" % (player.nickname, player.deaths, rounds),
                        'priority': 80,
                        'priority_multiplier': rounds / 10
        },
        'TOP_FRAGGER_LOWEST_LEVEL_IN_TEAM': {
                        'condition': await is_team_topfragger_but_lowest_level(player, player_team),
                        'description': "**%s** was the top fragger even though he was the lowest level in the team" % player.nickname,
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'BOTTOM_FRAGGER_HIGHEST_LEVEL_IN_TEAM': {
                        'condition': await is_team_bottomfragger_but_highest_level(player, player_team),
                        'description': "**%s** was the bottom fragger even though he was the highest level in the team" % player.nickname,
                        'priority': 70,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'TOP_FRAGGER_LOWEST_LEVEL_IN_MATCH': {
                        'condition': await is_match_topfragger_but_lowest_level(player, player_team, enemy_team),
                        'description': "**%s** was the top fragger even though he was the lowest level (%s) in the match" % (player.faceit_level, player.nickname),
                        'priority': 90,
                        'priority_multiplier': player.kd_ratio
                        },
        'BOTTOM_FRAGGER_HIGHEST_LEVEL_IN_MATCH': {
                        'condition': await is_match_topfragger_but_lowest_level(player, player_team, enemy_team),
                        'description': "**%s** was the bottom fragger even though he was the highest level (%s) in the match" % (player.faceit_level, player.nickname),
                        'priority': 90,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'MATCH_TOP_FRAGGER': {
                        'condition': await is_match_topfragger(player, player_team, enemy_team),
                        'description': "**%s** was the top fragger of the match with %s kills" % (player.nickname, player.kills),
                        'priority': 70,
                        'priority_multiplier': player.kd_ratio
                        },
        'MATCH_BOTTOM_FRAGGER': {
                        'condition': await is_match_bottomfragger(player, player_team, enemy_team),
                        'description': "**%s** was the bottom fragger of the match" % player.nickname,
                        'priority': 70,
                        'priority_multiplier': 1 + (player.deaths / 50)
                        },
        'MATCH_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / match_total_kills) * 100) >= 15,
                        'description': "**{0}** had **{1:.3g}**% of the match total kills ({2})".format(player.nickname, ((player.kills / match_total_kills) * 100), match_total_kills),
                        'priority': 60,
                        'priority_multiplier': 1 + (player.kills / match_total_kills)
                        },
        'TEAM_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / player_team_total_kills) * 100) >= 30,
                        'description': "**{0}** had **{1:.3g}**% of his teams total kills ({2})".format(player.nickname, ((player.kills / player_team_total_kills) * 100), player_team_total_kills),
                        'priority': 40,
                        'priority_multiplier': 1.2 + (player.kills / enemy_team_total_kills)
                        },
        'ENEMY_TEAM_KILLED_BIG_AMOUNT': {
                        'condition': ((player.kills / enemy_team_total_kills) * 100) >= 30,
                        'description': "**{0}** had **{1:.3g}**% of enemy teams total kills ({2})".format(player.nickname, ((player.kills / enemy_team_total_kills) * 100),
                                                                                                                         enemy_team_total_kills),
                        'priority': 30,
                        'priority_multiplier': 1.2 + (player.kills / enemy_team_total_kills)
                        },
        'MATCH_TOP_ASSISTER': {
                        'condition': await is_match_top_assister(player, player_team, enemy_team),
                        'description': "**%s** had the most assists (%s) in the match" % (player.nickname, player.assists),
                        'priority': 70,
                        'priority_multiplier': 1 + (player.assists / rounds)
                        },
        'TEAM_TOP_ASSISTER': {
                        'condition': await is_team_top_assister(player, player_team) and not await is_match_top_assister(player, player_team, enemy_team), #todo fix..
                        'description': "**%s** was the top assister of his team (%s assists)" % (player.nickname, player.assists),
                        'priority': 70,
                        'priority_multiplier': 1 + (player.assists / rounds)
        },
        'LONG_MATCH': {
                        'condition': ((match_length / rounds) >= 115),
                        'description': "rounds had an average length of **{0:.3g}** minutes".format(
                           (match_length / 60) / rounds),
                        'priority': 50,
                        'priority_multiplier': ((match_length / rounds) / 75)
                        },
        'MANY_KILLS_MULTI_KILLS': {
                        'condition': await has_many_kills_multi_kills(player),
                        'description': "**{0}** had **{1:.3g}**% of their kills consist(ed) of either triple, quad or penta kills ({2}t-{3}q-{4}p)".format(player.nickname,
                            ((((player.penta_kills * 5) + (player.quadro_kills * 4) + (player.triple_kills * 3)) / player.kills) * 100),  player.triple_kills, player.quadro_kills, player.penta_kills),
                        'priority': 50,
                        'priority_multiplier': rounds / 10
                         },
        'BIG_MVP_PERCENTAGE': {
                        'condition': ((player.mvps / rounds) * 100) >= 30,
                        'description': "**{0}** had **{1}**% mvp's (**{2:.3g}**% out of {3} rounds)".format(
                            player.nickname, player.mvps, ((player.mvps / rounds) * 100), rounds),
                        'priority': 90,
                        'priority_multiplier': rounds / 10
                        },
        'BAD_HEADSHOT_RATE': {
                        'condition': (player.headshots_perc <= 20) and (player.kills >= 20),
                        'description': "**{0}** had a headshot percentage of only **{1:.3g}**% ({2} of {3} kills)".format(
                            player.nickname, player.headshots_perc, player.headshots, player.kills),
                        'priority': 90,
                        'priority_multiplier': player.kills / 10
        },
        'HIGH_KR_RATIO': {
                        'condition': (player.kr_ratio >= 1.2) and (rounds >= 15),
                        'description': "**{0}** had an average of **{1}** kills per round".format(
                            player.nickname, player.kr_ratio),
                        'priority': 50,
                        'priority_multiplier': player.kr_ratio
        },
        'DIED_THE_MOST': {
                        'condition': await died_the_most(player, player_team, enemy_team),
                        'description': "**{0}** died the most times in the match ({1} times)".format(
                            player.nickname, player.deaths),
                        'priority': 50,
                        'priority_multiplier': player.deaths / 10
        },
        'TOP_FRAGGER_FEW_KILLS': {
                        'condition': player.rank == 1 and player.kr_ratio <= 0.7 and rounds >= 20,
                        'description': "**{0}** was the top fragger of his team with just **{1}** kills.".format(
                            player.nickname, player.kills),
                        'priority': 70,
                        'priority_multiplier': rounds / 10
        },
        'BOTTOM_FRAGGER_GOOD_KD': {
                        'condition': player.rank == 5 and player.kd_ratio >= 1.7 and rounds >= 10,
                        'description': "**{0}** was the bottom fragger of his team even though he had a kd ratio of **{1}**.".format(
                            player.nickname, player.kd_ratio),
                        'priority': 100,
                        'priority_multiplier': player.kd_ratio
        },
        'MATCH_DIED_BIG_AMOUNT': {
                        'condition': ((player.deaths / match_total_deaths) * 100) >= 15,
                        'description': "**{0}** had **{1:.3g}%** of the match's total deaths ({2}).".format(
                            player.nickname, (player.deaths / match_total_deaths) * 100, player.deaths),
                        'priority': 80,
                        'priority_multiplier': player.deaths / 10
        },
        'TEAM_DIED_BIG_AMOUNT': {
                        'condition': ((player.deaths / player_team_total_deaths) * 100) >= 30,
                        'description': "**{0}** had **{1:.3g}%** of his team's total deaths ({2}).".format(
                            player.nickname, (player.deaths / player_team_total_deaths) * 100, player.deaths),
                        'priority': 80,
                        'priority_multiplier': player.deaths / 10
        },
    }

    base_string = "**Match highlight(s)**: "
    highlight_string = ""

    occured_highlights = []
    occured_highlights_priorities = []

    for x in highlights:
        condition, description, priority, priority_multiplier = highlights.get(x).values()
        if condition:
            priority *= priority_multiplier
            occured_highlights.append(x)
            occured_highlights_priorities.append(priority)


    if not occured_highlights:
        return ""
    else:
        while len(occured_highlights) >= 1:
            chosen_highlight = random.choices(occured_highlights, occured_highlights_priorities)[0]
            chosen_highlight_description = highlights.get(chosen_highlight).get("description")
            del occured_highlights_priorities[occured_highlights.index(chosen_highlight)]
            occured_highlights.remove(chosen_highlight)
            if highlight_string:
                highlight_string += " and" + chosen_highlight_description.replace("**" + player.nickname + "**", "")
                if highlight_string[0:50].find("had") != -1: # todo: fix this
                    highlight_string = highlight_string.replace("and had", "and")
                return highlight_string
            else:
                highlight_string += base_string + chosen_highlight_description
        else:
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