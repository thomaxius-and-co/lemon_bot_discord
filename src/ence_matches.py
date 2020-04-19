import lxml.html as lh
import pandas
import cfscrape
from tablemaker import tablemaker
import logger
import datetime
import util
from time_util import to_helsinki, as_utc
import database as db
from copy import deepcopy
from asyncio import sleep

log = logger.get("ENCE")

FETCH_INTERVAL = 9000

MATCHES_DICT = {}
LAST_CHECKED = None
UNDEFINED_MATCHES_COUNT = 0
LAST_SPAMMED = None
ENCE_HLTV_MATCHES_LIST_URL = "https://www.hltv.org/matches?team=4869"

hltv_maps = {
    'cch': 'de_cache',
    'mrg': 'de_mirage',
    'd2': 'de_dust2',
    'nuke': 'de_nuke',
    'ovp': 'de_overpass',
    'inf': 'de_inferno',
    'trn': 'de_train',
    'vtg': 'de_vertigo'
}

# todo: fetch teams from both sites instead

async def do_tasks(client):
    while True:
        global MATCHES_DICT
        MATCHES_DICT.clear()
        await parse_hltv_matches(await get_hltv_matches())
        global LAST_CHECKED
        LAST_CHECKED = datetime.datetime.now()
        await check_if_ence_day(client)
        await sleep(FETCH_INTERVAL)


async def check_if_ence_day(client):
    log.info("Checking if match day")
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    matches_today = MATCHES_DICT.get(now.date(), None)
    if matches_today:
        if LAST_SPAMMED:
            if (LAST_SPAMMED.date() != now.date()): #If already spammed today
                await do_matchday_spam(client, matches_today)
        else:
            await do_matchday_spam(client, matches_today)
    else:
        log.info('No matches today')


async def get_all_spam__channels():
    return await db.fetch("""
        SELECT channel_id
        FROM faceit_notification_channel
    """)


async def update_last_spammed_time():
    global LAST_SPAMMED
    LAST_SPAMMED = datetime.datetime.now()

async def do_matchday_spam(client, matches):
    channels_query = await get_all_spam__channels() # Using faceit spam channel for now
    matches_list = []
    if not channels_query:
        log.info('No spam channels have been set')
        return
    for row in channels_query:
        channel = util.threadsafe(client, client.fetch_channel(int(row['channel_id'])))
        if len(matches) > 1:
            msg = "It is match day!\nToday we have %s matches:\n" % len(matches)
        else:
            msg = "It is match day! Today we have:\n"
        for match in matches:
            match_as_row = convert_to_list(match)
            if match_as_row not in matches_list:
                matches_list += [match_as_row] # Competition, Home team, away team, map, tod
        util.threadsafe(client, channel.send(msg + "```" + tablemaker.tablemaker(['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'TOD'], matches_list) + "\n#EZ4ENCE```"))
    await update_last_spammed_time()
    if channels_query and matches[0][6] != '-':
        await start_match_start_spam_task(client, channels_query, matches[0])

async def not_rescheduled(match_item):
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    matches = MATCHES_DICT.get(now.date(), None)
    log.info('match_item = %s, matches[0] = %s' % (match_item, matches[0]))
    return matches[0] != match_item



async def start_match_start_spam_task(client, channels_query, earliest_match): # todo: maybe make a 'spam function' which can be used by both functions
    match_time = earliest_match[5]
    match = as_utc(match_time).replace(tzinfo=None)
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    delta = max((match - now - datetime.timedelta(seconds=900)), datetime.timedelta(seconds=0))
    log.info('Match spammer task: going to sleep for %s seconds' % delta.seconds)
    await sleep(delta.seconds)
    log.info('Match spammer task: waking up and attempting to spam')
    if await not_rescheduled(earliest_match):
        for row in channels_query:
            channel = util.threadsafe(client, client.fetch_channel(int(row['channel_id'])))
            util.threadsafe(client, channel.send(("The %s match %s versus %s is about to start! (announced starting time: %s) \n#EZ4ENCE" % (earliest_match[0], earliest_match[1], earliest_match[2], earliest_match[6]))))
        await update_last_spammed_time()
        # todo: fire up do_tasks after this function
        # todo: fix this and spam about new match time if match is rescheduled


async def get_hltv_matches():
    log.info("Fetching HLTV matches")
    scraper = cfscrape.create_scraper()
    page = scraper.get(ENCE_HLTV_MATCHES_LIST_URL)
    if page.status_code != 200:
        log.info("Failed to fetch HLTV matches. Error code %s" % page.status_code)
        return
    doc = lh.fromstring(page.content)
    upcoming_hltv_matches_elements = doc.xpath('//div[@class="match-day"]//table')  # Get match tables
    log.info("Fetched %s HLTV matches." % len(upcoming_hltv_matches_elements))
    return upcoming_hltv_matches_elements


async def parse_hltv_matches(match_elements):
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    if match_elements:
        for element in match_elements:
            date = to_helsinki(as_utc(pandas.to_datetime((int(element[0][0][0].values()[2])),unit='ms'))).replace(tzinfo=None)  # table -> tr -> td -> div
            date = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
            if date < now:
                log.info('HLTV Match already started or played, not adding it to matches dict')
                continue
            home_team = element[0][1].text_content().replace('\n','').strip() # table -> tr -> div -> div>
            away_team = element[0][3].text_content().replace('\n', '').strip()
            competition = element[0][4].text_content().replace('\n', '').strip()
            map = element[0][5].text_content().replace('\n', '').strip()
            if map in ["bo1", "bo2", "bo3", "bo4", "bo5"]:
                map = "TBD (%s)" % map
            tod = ('%s:%s' % (date.hour, (str(date.minute)) if date.minute != 0 else str(date.minute) + "0"))
            item = {'competition': competition[:15], 'home_team': home_team, 'away_team': away_team, 'map': map, 'status': 'Upcoming', 'date': date, 'tod': tod}
            matches_for_date = MATCHES_DICT.get(date.date(), None)
            if matches_for_date:
                if await not_added(item, matches_for_date):
                    matches_for_date.append(item)
                else:
                    log.info('HLTV Match is already added')
            else:
                MATCHES_DICT.update({date.date():[item]})
    log.info("HLTV matches parsed.")

async def not_added(comparsion_match, matches):
    for match in matches:
        log.info('match: %s, comparsion_match %s' % (matches, comparsion_match))
        if match[0] == comparsion_match[0] and match[1] == comparsion_match[1] and match[2] == comparsion_match[2] \
                and match[3] == comparsion_match[3] and match[4] == comparsion_match[4] and match[5].date() == comparsion_match[5].date():
            return False
    return True


async def convert_to_list(match_dict: dict, convert_date_to_str=True) -> list:
        competition, home_team, away_team, map, status, date, tod = match_dict.get('competition'), match_dict.get(
            'home_team'), match_dict.get('away_team'), match_dict.get('map'), match_dict.get('status'), match_dict.get('date'), match_dict.get(
            'tod')
        if convert_date_to_str:
            date = str(date.date())
        return [competition, home_team, away_team, map, status, date, tod]


async def cmd_ence(client, message, arg):
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    if not LAST_CHECKED:
        await message.channel.send("https://i.ytimg.com/vi/CRvlTjeHWzA/maxresdefault.jpg\n(Matches haven't been fetched yet as the bot was just started, please try again soon)")
    else:
        list_of_matches = deepcopy([x for y in sorted(MATCHES_DICT.values(), key=lambda x: x[0].get('date')) for x in y])
        list_of_matches = [await convert_to_list(match_dict) for match_dict in list_of_matches if match_dict.get('date') > now]
        await message.channel.send((("\nAs of %s: ```" % to_helsinki(as_utc(LAST_CHECKED)).strftime(
            "%Y-%m-%d %H:%M")) + tablemaker(
            ['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE', 'TOD']
            , list_of_matches) + "\n#EZ4ENCE```"))


def register(client):
    util.start_task_thread(do_tasks(client))
    return {
        'ence': cmd_ence,
    }



