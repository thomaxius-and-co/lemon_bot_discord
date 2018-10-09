import lxml.html as lh
import pandas
import cfscrape
import columnmaker
import logger
import datetime
import util
from time_util import to_helsinki, as_utc, as_helsinki, to_utc
import discord
import database as db
from copy import deepcopy
from asyncio import sleep

log = logger.get("ENCE")

FETCH_INTERVAL = 9000

MATCHES_DICT = {}
LAST_CHECKED = None
UNDEFINED_MATCHES_COUNT = 0
LAST_SPAMMED = None


async def do_tasks(client):
    while True:
        await parse_hltv_matches(await get_hltv_matches())
        await parse_mdl_matches(await get_mdl_matches())
        await remove_played_matches()
        global LAST_CHECKED
        LAST_CHECKED = datetime.datetime.now()
        await check_if_ence_day(client)
        await sleep(FETCH_INTERVAL)


async def check_if_ence_day(client):
    log.info("Checking if match day")
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    matches = MATCHES_DICT.get(now.date(), None)
    if matches:
        if LAST_SPAMMED:
            if (LAST_SPAMMED.date() != now.date()): #If already spammed today
                await do_matchday_spam(client, matches)
        else:
            await do_matchday_spam(client, matches)
    else:
        log.info('No matches today')


async def get_all_spam__channels():
    return await db.fetch("""
        SELECT channel_id
        FROM faceit_notification_channel
    """)


async def remove_played_matches():
    global MATCHES_DICT
    log.info('Removing possible played matches')
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    new_dict = deepcopy(MATCHES_DICT)
    for matchday, matches in MATCHES_DICT.items():
        new_dict[matchday] = ([x for x in matches if x[5] > now]) # x[5] = datetime
        if not new_dict[matchday]:
            log.info('Removing matches of day %s' % matchday)
            new_dict.clear()
    MATCHES_DICT = new_dict


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
        channel = discord.Object(id=row['channel_id'])
        if len(matches) > 1:
            msg = "It is match day!\nToday we have %s matches:\n" % len(matches)
        else:
            msg = "It is match day! Today we have:\n"
        for match in matches:
            item = [match[0], match[1], match[2], match[3], match[6]]
            if item not in matches_list:
                matches_list += [item] # Competition, Home team, away team, map, tod

        util.threadsafe(client, client.send_message(channel, msg + "```" + columnmaker.columnmaker(['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'TOD'], matches_list) + "\n#EZ4ENCE```"))
    await update_last_spammed_time()
    if channels_query and matches[0][6] != '-':
        await start_match_start_spam_task(client, channels_query, matches[0])


async def start_match_start_spam_task(client, channels_query, earliest_match): # todo: maybe make a 'spam function' which can be used by both functions
    match_time = earliest_match[5]
    match = as_utc(match_time).replace(tzinfo=None)
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    delta = max((match - now - datetime.timedelta(seconds=900)), datetime.timedelta(seconds=0))
    log.info('Match spammer task: going to sleep for %s seconds' % delta.seconds)
    await sleep(delta.seconds)
    log.info('Match spammer task: waking up and attempting to spam')
    for row in channels_query:
        channel = discord.Object(id=row['channel_id'])
        util.threadsafe(client, client.send_message(channel, ("The %s match %s versus %s is about to start! (announced starting time: %s) \n#EZ4ENCE" % (earliest_match[0], earliest_match[1], earliest_match[2], earliest_match[6]))))
    await update_last_spammed_time()
    # todo: fire up do_tasks after this function


async def get_mdl_matches():
    log.info("Fetching MDL matches")
    scraper = cfscrape.create_scraper()
    page = scraper.get("https://play.esea.net/teams/82159")
    if page.status_code != 200:
        log.info("Failed to fetch MDL matches. Error code %s" % page.status_code)
        return
    doc = lh.fromstring(page.content)
    tr_elements = doc.xpath('//tr')  # Get table elements
    #Fetch only matches that have map as Pending veto or  result as 'Upcoming (0)'
    upcoming_mdl_matches_elements = [element for element in tr_elements[1:] if (element[4].text_content() == 'Upcoming (0)') or (element[3].text_content() == 'Pending Veto')]
    log.info("Fetched %s MDL matches." % len(upcoming_mdl_matches_elements))
    return upcoming_mdl_matches_elements


async def get_hltv_matches():
    log.info("Fetching HLTV matches")
    scraper = cfscrape.create_scraper()
    page = scraper.get("https://www.hltv.org/matches?team=4869")
    if page.status_code != 200:
        log.info("Failed to fetch HLTV matches. Error code %s" % page.status_code)
        return
    doc = lh.fromstring(page.content)
    upcoming_hltv_matches_elements = doc.xpath('//div[@class="match-day"]//table')  # Get match tables
    log.info("Fetched %s HLTV matches." % len(upcoming_hltv_matches_elements))
    return upcoming_hltv_matches_elements


async def parse_hltv_matches(match_elements):
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    for element in match_elements:
        date = to_helsinki(as_utc(pandas.to_datetime((int(element[0][0][0].values()[2])),unit='ms'))).replace(tzinfo=None)  # table -> tr -> td -> div
        date = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
        if date < now:
            log.info('Match already started or played, not adding it to matches dict')
            continue
        home_team = element[0][1].text_content().replace('\n','').strip() # table -> tr -> div -> div>
        away_team = element[0][3].text_content().replace('\n', '').strip()
        competition = element[0][4].text_content().replace('\n', '').strip()
        map = element[0][5].text_content().replace('\n', '').strip()
        if map in ["bo1", "bo2", "bo3", "bo4", "bo5"]:
            map = "TBD (%s)" % map
        tod = ('%s:%s' % (date.hour, (str(date.minute)) if date.minute != 0 else str(date.minute) + "0"))
        item = [competition[:10], home_team, away_team, map, 'Upcoming', date, tod]
        if MATCHES_DICT.get(date.date(), None):
            MATCHES_DICT.get(date.date()).append(item)
        else:
            MATCHES_DICT.update({date.date():[item]})
    log.info("HLTV matches parsed.")


async def parse_mdl_matches(match_elements):
    now = to_helsinki(as_utc(datetime.datetime.now())).replace(tzinfo=None)
    global UNDEFINED_MATCHES_COUNT
    UNDEFINED_MATCHES_COUNT = 0
    for element in match_elements:
        home_team = element[1].text_content() if element[1].text_content() != '-' and element[1].text_content() else 'TBD'
        away_team = element[2].text_content() if element[2].text_content() != '-' and element[2].text_content() else 'TBD'
        map = element[3].text_content() if element[3].text_content() != '-' and element[3].text_content() else 'TBD'
        status = element[4].text_content().replace('Upcoming (0)', 'Upcoming') if element[4].text_content() != '-' and element[4].text_content() else 'Unconfirmed'
        date = element[len(element)-1].text_content().replace('\n','').replace('\r','').strip() #element lenght varies
        if date != '-' and date:
            try:
                date = datetime.datetime.strptime(date, "%b %d %y")
            except ValueError:
                date = datetime.datetime.strptime(date, "%b %d, %I:%M%p").replace(year=datetime.datetime.now().year)
        else:
            date = 'TBD'
        if date != 'TBD':
            if date < now:
                log.info('Match already started, not adding it to matches dict')
                continue
        tod = '-' # Even though some MDL matches have time of day, I  don't think It's very reliable, considering
        #  they're set for weeks before the match is even confirmed. Instead, We will fetch time of day when it is match day.
        item = ['MDL', home_team, away_team, map, status, date, tod]
        if (home_team == 'TBD') and (away_team == 'TBD') and (status != 'Upcoming'): # I think It's pointless to show matches that have no confirmed teams or maps yet.
            UNDEFINED_MATCHES_COUNT += 1
            continue
        if MATCHES_DICT.get(date.date(), None):
            if item not in MATCHES_DICT.get(date.date()):
                MATCHES_DICT.get(date.date()).append(item)
        else:
            MATCHES_DICT.update({date.date():[item]})
    log.info("MDL matches parsed.")


async def cmd_ence(client, message, arg):
    if not LAST_CHECKED:
        await client.send_message(message.channel,
                                  "https://i.ytimg.com/vi/CRvlTjeHWzA/maxresdefault.jpg\n(Matches haven't been fetched yet as the bot was just started, please try again soon)")
    else:
        list_of_matches = deepcopy([x for y in sorted(MATCHES_DICT.values(), key=lambda x: x[0][5]) for x in y])

        def convert_date(x):
            x[5] = x[5].date()
            return x
        list_of_matches = [convert_date(x) for x in list_of_matches]
        await client.send_message(message.channel, (("\nAs of %s: ```" % to_helsinki(as_utc(LAST_CHECKED)).strftime(
            "%Y-%m-%d %H:%M")) + columnmaker.columnmaker(
            ['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE', 'TOD']
            , list_of_matches) + ("\n+ %s pending MDL matches" % (UNDEFINED_MATCHES_COUNT)) + "\n#EZ4ENCE```"))


def register(client):
    util.start_task_thread(do_tasks(client))
    return {
        'ence': cmd_ence,
    }



