import requests
import lxml.html as lh
import pandas as pd
import cfscrape
import columnmaker
import logger
import datetime
import util
from time_util import to_helsinki, as_utc
from time import sleep

log = logger.get("ENCE")

UPCOMING_MATCHES_ELEMENTS = []
UPCOMING_HLTV_MATCHES_ELEMENTS = []
UNDEFINED_MATCHES = 0
LAST_CHECKED = None


async def main():
    log.info("Initializing")
    await get_mdl_matches()


async def get_mdl_matches():
    while True:
        log.info("Fetching ence matches")
        scraper = cfscrape.create_scraper()
        page = scraper.get("https://play.esea.net/teams/82159")
        if page.status_code != 200:
            log.info("Failed to fetch matches. Error code %s" % page.status_code)
            return
        doc = lh.fromstring(page.content)
        tr_elements = doc.xpath('//tr')  # Get table rows
        global UPCOMING_MATCHES_ELEMENTS  #Fetch only matches that have map as Pending veto or  result as 'Upcoming (0)'
        UPCOMING_MATCHES_ELEMENTS = [element for element in tr_elements[1:] if (element[4].text_content() == 'Upcoming (0)') or (element[3].text_content() == 'Pending Veto')]
        global LAST_CHECKED
        LAST_CHECKED = datetime.datetime.now()
        log.info("Fetched %s MDL matches." % len(UPCOMING_MATCHES_ELEMENTS))
        await sleep(36000)


async def get_hltv_matches():
        while True:
            log.info("Fetching ence matches")
            scraper = cfscrape.create_scraper()
            page = scraper.get("https://www.hltv.org/matches?team=4869")
            doc = lh.fromstring(page.content)
            global UPCOMING_HLTV_MATCHES_ELEMENTS
            UPCOMING_HLTV_MATCHES_ELEMENTS = doc.xpath('//div[@class="match-day"]//table')  # Get match tables
            log.info("Fetched %s HLTV matches." % len(UPCOMING_HLTV_MATCHES_ELEMENTS))
            await sleep(36000)


async def parse_hltv_matches():
    upcoming_matches_list = []
    for row in UPCOMING_HLTV_MATCHES_ELEMENTS:
        date = to_helsinki(as_utc(datetime.datetime.fromtimestamp(row[0][0][0].values()[2])).strftime("%d/%m/%y %H:%M"))  # table -> tr -> td -> div
        home_team = row[0][1].text_content().replace('\n','').strip() # table -> tr -> div -> div>
        away_team = row[0][3].text_content().replace('\n', '').strip()
        competition = row[0][4].text_content().replace('\n', '').strip()
        map = row[0][5].text_content().replace('\n', '').strip()
        item = (competition, home_team, away_team, map, 'Upcoming', date)
        log.info(item)
        upcoming_matches_list.append(item)
    return upcoming_matches_list


async def parse_mdl_matches():
    upcoming_matches_list = []
    undefined_matches_count = 0
    for row in UPCOMING_MATCHES_ELEMENTS:
        home_team = row[1].text_content() if row[1].text_content() != '-' and row[1].text_content() else 'TBD'
        away_team = row[2].text_content() if row[2].text_content() != '-' and row[2].text_content() else 'TBD'
        map = row[3].text_content() if row[3].text_content() != '-' and row[3].text_content() else 'TBD'
        status = row[4].text_content().replace('Upcoming (0)', 'Upcoming') if row[4].text_content() != '-' and row[4].text_content() else 'Unconfirmed'
        date = row[len(row)-1].text_content().replace('\n','').replace('\r','').strip() #row lenght varies
        if date != '-' and date:
            try:
                date = datetime.datetime.strptime(date, "%b %d %y").date()
            except ValueError:
                date = datetime.datetime.strptime(date, "%b %d, %I:%M%p").replace(year=datetime.datetime.now().year).date()
        else:
            date = 'TBD'
        item = ('MDL', home_team, away_team, map, status, date)
        if item not in upcoming_matches_list and (home_team != 'TBD') and (away_team != 'TBD'):
            upcoming_matches_list.append(item)
        if (home_team == 'TBD') and (away_team == 'TBD') and (status != 'Upcoming'): # I think It's pointless to show matches that have no confirmed teams or maps yet.
            undefined_matches_count += 1
    return upcoming_matches_list, undefined_matches_count


async def cmd_ence(client, message, arg):
        upcoming_hltv_matches_list = await parse_hltv_matches()
        upcoming_mdl_matches_list, undefined_matches_count = await parse_mdl_matches()
        full_list_of_matches = sorted(upcoming_hltv_matches_list + upcoming_mdl_matches_list, key=lambda x: x[5])
        if not full_list_of_matches:
            await client.send_message(message.channel, "https://i.ytimg.com/vi/CRvlTjeHWzA/maxresdefault.jpg")
        else:
            await client.send_message(message.channel, (("\nAs of %s: ```" % to_helsinki(as_utc(LAST_CHECKED)).strftime("%Y-%m-%d %H:%M")) + columnmaker.columnmaker(['COMPETITION', 'HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE']
                                                                     , full_list_of_matches) + ("\n+ %s pending matches" % (undefined_matches_count)) + "\n#EZ4ENCE```"))

def register(client):
    util.start_task_thread(main())
    return {
        'ence': cmd_ence,
    }



