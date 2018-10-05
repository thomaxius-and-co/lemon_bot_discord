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
UNDEFINED_MATCHES = 0
LAST_CHECKED = None


async def main():
    log.info("Initializing")
    await get_matches()


async def get_matches():
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
        log.info("Fetched %s matches." % len(UPCOMING_MATCHES_ELEMENTS))
        await sleep(36000)


async def parse_matches():
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
        item = (home_team, away_team, map, status, date)
        if item not in upcoming_matches_list and (home_team != 'TBD') and (away_team != 'TBD'):
            upcoming_matches_list.append(item)
        if (home_team == 'TBD') and (away_team == 'TBD') and (status != 'Upcoming'): # I think It's pointless to show matches that have no confirmed teams or maps yet.
            undefined_matches_count += 1
    return sorted(upcoming_matches_list, key=lambda x: x[4]), undefined_matches_count


async def cmd_ence(client, message, arg):
        upcoming_matches_list, undefined_matches_count = await parse_matches()
        if not upcoming_matches_list:
            await client.send_message(message.channel, "https://i.ytimg.com/vi/CRvlTjeHWzA/maxresdefault.jpg")
        else:
            await client.send_message(message.channel, (("\nAs of %s: ```" % to_helsinki(as_utc(LAST_CHECKED)).strftime("%Y-%m-%d %H:%M")) + columnmaker.columnmaker(['HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE']
                                                                     , upcoming_matches_list) + ("\n+ %s pending matches" % (undefined_matches_count)) + "\n#EZ4ENCE```"))

def register(client):
    util.start_task_thread(main())
    return {
        'ence': cmd_ence,
    }



