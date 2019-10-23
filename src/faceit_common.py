import logger
import faceit_db_functions as faceit_db
import faceit_api
from faceit_api import NotFound, UnknownError
log = logger.get("FACEIT_COMMON")


async def do_nick_change_check(guid, api_player_name, database_player_name):
    log.info("Checking nickname changes for user %s %s" % (guid, database_player_name))
    if api_player_name != database_player_name:
        log.info("Nickname change detected for user %s: old %s, new %s" % (guid, database_player_name, api_player_name))
        await faceit_db.update_nickname(guid, api_player_name)
    else:
        log.info("No nickname changes detected for user %s " % guid)
        return

async def get_matches(player_guid, from_timestamp, to_timestamp=None):
    try:
        return await faceit_api.player_match_history(player_guid, from_timestamp, to_timestamp)
    except NotFound as e:
        log.error(e)
        return None

# Combines match stats and match details (from two different api endpoints) to a dict
async def get_combined_match_data(matches):
    combined = {}
    for match in matches:
        match_id = match.get("match_id")
        match_details = await faceit_api.match(match_id)
        if match_details is None:
            log.warning("Match details not available, skipping.. (match_id: %s)" % match_id)
            continue
        if match_details.get("game") != 'csgo':
            log.info("Match is not csgo, skipping.. %s" % match_details) # Faceit api is so much fun that there aren't
            # just csgo matches in the csgo endpoints
            continue
        elif not match_details:
            log.warning("Match details not available, skipping.. %s" % match_details)
            continue
        match_stats = await faceit_api.match_stats(match_id)
        if not match_stats:
            log.info("Match stats not available, skipping.. %s" % match_details)
            continue
        combined.update({match_id: {
                                    'match_details': match_details,
                                    'match_stats': match_stats[0]
                                    }
                        })
    return combined


async def get_user_stats_from_api_by_id(player_id):
    try:
        user = await faceit_api.user_by_id(player_id)
        player_id = user.get("player_id")
        last_activity = await latest_match_timestamp(player_id)
    except NotFound as e:
        log.error(str(e))
        return None, None, None, None, None
    except UnknownError as e:
        if e.response.status >= 500:
            log.warning("Unknown error: {0}".format(str(e)))
        else:
            log.error("Unknown error: {0}".format(str(e)))
        return None, None, None, None, None

    csgo = user.get("games", {}).get("csgo", {})
    nickname = user.get("nickname", None)  # Is this even needed
    skill_level = csgo.get("skill_level", None)
    csgo_elo = csgo.get("faceit_elo", None)
    ranking = await faceit_api.ranking(player_id) if csgo_elo else None
    return csgo_elo, skill_level, nickname, ranking, last_activity


def flat_map(func, xs):
    from itertools import chain
    return list(chain.from_iterable(map(func, xs)))


def max_or(xs, fallback):
    return max(xs) if len(xs) > 0 else fallback


async def latest_match_timestamp(player_id):
    json = await faceit_api.player_history(player_id)
    matches = json.get("items")
    timestamps = flat_map(lambda m: [m.get("started_at"), m.get("finished_at")], matches)
    return max_or(timestamps, None)