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