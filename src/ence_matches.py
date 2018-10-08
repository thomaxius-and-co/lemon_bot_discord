import requests
import lxml.html as lh
import pandas
import cfscrape
import columnmaker
import logger
import datetime
import util
from time_util import to_helsinki, as_utc
from time import sleep
import discord
import database as db
import copy
log = logger.get("ENCE")

MATCHES_DICT = {}
LAST_CHECKED = None
FETCH_INTERVAL = 18000
UNDEFINED_MATCHES_COUNT = 0
LAST_SPAMMED = None

async def do_match_check(client):
    while True:
        global MATCHES_DICT
        await parse_hltv_matches(await get_hltv_matches())
        await parse_mdl_matches(await get_mdl_matches())
        global LAST_CHECKED
        LAST_CHECKED = datetime.datetime.now()
        await check_if_ence_day(client)
        await sleep(FETCH_INTERVAL)

async def check_if_ence_day(client):
    log.info("Checking if match day")


    matches = MATCHES_DICT.get(datetime.datetime.now().date(), None)
    if matches:
        if LAST_SPAMMED:
            if (LAST_SPAMMED.date() != datetime.datetime.now().date()): #If already spammed today
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


async def do_matchday_spam(client, matches):
    channels_query = await get_all_spam__channels() # Using faceit spam channel for now
    if not channels_query:
        log.info('No spam channels have been set')
        return
    for row in channels_query:
        channel = discord.Object(id=row['channel_id'])
        matches_list = []
        if len(matches) > 1:
            msg = "It is match day!\nToday we have %s matches:\n" % len(matches)
        else:
            msg = "It is match day! Today we have:\n"
        for match in matches:
            matches_list += [[match[0], match[1], match[2], match[3], match[6]]] # Competition, Home team, away team, map, tod
        log.info(matches_list)
        util.threadsafe(client, client.send_message(channel, msg + "```" + columnmaker.columnmaker(['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'TOD'], sorted(matches_list, key= lambda x: x[4])) + "\n#EZ4ENCE```"))
    global LAST_SPAMMED
    LAST_SPAMMED = datetime.datetime.now()


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
    for element in match_elements:
        date = to_helsinki(as_utc(pandas.to_datetime((int(element[0][0][0].values()[2])),unit='ms'))).replace(tzinfo=None)  # table -> tr -> td -> div
        date = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
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
        list_of_matches = copy.deepcopy([x for y in sorted(MATCHES_DICT.values(), key=lambda x: x[0][5]) for x in y])

        def convert_date(x):
            x[5] = x[5].date()
            return x
        list_of_matches = [convert_date(x) for x in list_of_matches]
        await client.send_message(message.channel, (("\nAs of %s: ```" % to_helsinki(as_utc(LAST_CHECKED)).strftime(
            "%Y-%m-%d %H:%M")) + columnmaker.columnmaker(
            ['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE', 'TOD']
            , list_of_matches) + ("\n+ %s pending MDL matches" % (UNDEFINED_MATCHES_COUNT)) + "\n#EZ4ENCE```"))


def register(client):
    util.start_task_thread(do_match_check(client))
    return {
        'ence': cmd_ence,
    }



