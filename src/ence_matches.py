import requests
import lxml.html as lh
import pandas as pd
import cfscrape
import columnmaker
import logger

log = logger.get("ENCE")

upcoming_matches_elements = []

async def initialize():
        log.info("Initializing ence matches")
        scraper = cfscrape.create_scraper()
        page = scraper.get("https://play.esea.net/teams/82159")
        doc = lh.fromstring(page.content)
        tr_elements = doc.xpath('//tr')

        global upcoming_matches_elements
        upcoming_matches_elements = [element for element in tr_elements[1:] if (
                        (element[4].text_content() == 'Upcoming (0)') or (element[3].text_content() == 'Pending Veto'))]
        log.info("Ence matches fetched. Or at least I tried to fetch them.")


async def cmd_ence(client, message, arg):
        upcoming_matches_list = []
        for row in upcoming_matches_elements:
                home_team = row[1].text_content() if row[1].text_content() != '-' and row[1].text_content() else 'TBD'
                away_team = row[2].text_content() if row[2].text_content() != '-' and row[1].text_content() else 'TBD'
                map = row[3].text_content() if row[3].text_content() != '-' and row[1].text_content() else 'TBD'
                status = row[4].text_content() if row[4].text_content() != '-' and row[1].text_content() else 'TBD'
                date = row[5].text_content().replace('\n','').replace('\r','').lstrip().rstrip() if row[5].text_content() != '-' \
                                                                                                    and row[1].text_content() else 'TBD'
                item = (home_team, away_team, map, status, date)
                if item not in upcoming_matches_list:
                    upcoming_matches_list.append(item)

        await client.send_message(message.channel, "```" + columnmaker.columnmaker(['HOME TEAM', 'AWAY TEAM', 'MAP', 'STATUS', 'DATE']
                                                                     , upcoming_matches_list) + "\n\n#EZ4ENCE```")

def register(client):
    return {
        'ence': cmd_ence,
    }



