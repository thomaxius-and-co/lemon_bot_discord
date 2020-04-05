import logger
from datetime import datetime, timedelta
import aiohttp
import traceback

log = logger.get("CORONA")

CORONA_API_BASE_URL = 'https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/'
GENERAL_DATA_HANDLER = 'finnishCoronaData/v2'
HOSPITALISED_DATA_HANDLER = 'finnishCoronaHospitalData'

# Source: https://dvv.fi/
POPULATION_OF_FINLAND = 5_544_152

# Source: https://www.hs.fi/kotimaa/art-2000006425877.html
ICU_CAPACITY = 230

# Source: Thomaxius
WARD_CAPACITY = 800


async def _call_api(url: str) -> aiohttp.client_reqrep.ClientResponse:
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.debug("%s %s %s %s", response.method, response.url, response.status, await response.text())
        if response.status not in [200, 404]:
            raise Exception('Error fetching from corona api')
        return response


async def parse_date(datestr: str) -> datetime:
    return datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S.%fZ')


async def daily_stats(cases: list, comparsion_date: datetime) -> list:
    return [x for x in cases if datetime.strptime(x.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ').date() == comparsion_date.date()]


async def infected_stats(json: dict):
    yesterday = datetime.today() - timedelta(days=1)
    two_days_ago = datetime.today() - timedelta(days=2)
    confirmed_cases = json.get('confirmed')
    total_infections_amount, date_last_infected, new_infections, previous_infections = len(confirmed_cases), await parse_date(confirmed_cases[-1].get('date')), await daily_stats(confirmed_cases, yesterday), await daily_stats(confirmed_cases, two_days_ago)
    return total_infections_amount, date_last_infected, len(new_infections), len(previous_infections)


async def infections_count_difference_string(infections_after: int, infections_before: int) -> str:
    operator = ''
    difference = infections_after - infections_before
    if difference == 0:
        return ''
    if difference > 0:
        operator = '+'
    return '({0}{1})'.format(operator, difference)


async def get_corona_stats() -> [int, datetime, int, int, int, int]:
    response = await _call_api(CORONA_API_BASE_URL + GENERAL_DATA_HANDLER)
    json = await response.json()
    total_infections_amount, date_last_infected, new_infections, previous_infections = await infected_stats(json)
    recovered_amount = len(json.get('recovered'))
    deaths_amount = len(json.get('deaths'))
    return total_infections_amount, date_last_infected, new_infections, previous_infections, recovered_amount, deaths_amount


async def latest_hospitalised_stats_by_day(json: dict, area='Finland', search_date=datetime.today().date() - timedelta(days=1)) -> [int, int, int]:
    data = json.get('hospitalised')
    data_day = [x for x in data if x.get('area') == area and (await parse_date(x.get('date'))).date() == search_date][0]
    total_hospitalised, total_in_ward, total_in_icu, total_deaths = data_day.get('totalHospitalised'), data_day.get('inWard'), data_day.get('inIcu'), data_day.get('dead')
    return total_hospitalised, total_in_ward, total_in_icu, total_deaths


async def get_hospitalised() -> [int, int, int]:
    response = await _call_api(CORONA_API_BASE_URL + HOSPITALISED_DATA_HANDLER)
    json = await response.json()
    return await latest_hospitalised_stats_by_day(json)


async def cmd_corona(client, message, _) -> None:
    try:
        total_infections_amount, date_last_infected, infections_yesterday, infections_two_days_ago, recovered_amount, deaths_amount = await get_corona_stats()
        total_hospitalised, total_in_ward, total_in_icu, _ = await get_hospitalised()
        mortality_rate = deaths_amount / total_infections_amount
        percentage_of_people_to_get_infected = 40
        total_infections_over_time = POPULATION_OF_FINLAND * (percentage_of_people_to_get_infected / 100)
        total_deaths_over_time = round(total_infections_over_time * mortality_rate)
        await message.channel.send("\n".join([
            "**Corona statistics of Finland**",
            "**New infections yesterday:**: {0} {1}".format(infections_yesterday, await infections_count_difference_string(infections_yesterday, infections_two_days_ago)),
            "**Total infected**: {0}".format(total_infections_amount),
            "**Total recovered:** {0}".format(recovered_amount),
            "**Total hospitalised: {0}** (**{1}/{2}** in ICU, **{3}/{4}** in ward)".format(total_hospitalised, total_in_icu, ICU_CAPACITY, total_in_ward, WARD_CAPACITY),
            "**Total deaths:** {0}".format(deaths_amount),
            "**Mortality rate:** {0:.2f}%".format(mortality_rate * 100),
            "**Deaths if {0:.2f}% of population get infected:** {1}".format(percentage_of_people_to_get_infected, total_deaths_over_time),
            "**Last infection case:** {0}".format(date_last_infected.strftime('%Y-%m-%d %H:%M')),
        ]))
    except Exception:
        log.error(traceback.format_exc())
        await message.channel.send('There was an error fetching corona stats.')


def register(client) -> ():
    return {
        "corona": cmd_corona
    }
