import logger
import datetime
import aiohttp

log = logger.get("CORONA")

CORONA_API_URL = 'https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData'

# Source: https://dvv.fi/
POPULATION_OF_FINLAND = 5_544_152

async def _call_api(url):
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        log.debug("%s %s %s %s", response.method, response.url, response.status, await response.text())
        if response.status not in [200, 404]:
            raise Exception('Error fetching from corona api')
        return response


async def infected_stats(json):
    amount, date_last_infected = len(json.get('confirmed')), datetime.datetime.strptime(json.get('confirmed')[-1].get('date'), '%Y-%m-%dT%H:%M:%S.%f%z')
    return amount, date_last_infected

async def get_corona_stats():
    response = await _call_api(CORONA_API_URL)
    json = await response.json()
    infected_amount, last_infected_date = await infected_stats(json)
    recovered_amount = len(json.get('recovered'))
    deaths_amount = len(json.get('deaths'))
    return infected_amount, last_infected_date, recovered_amount, deaths_amount

async def cmd_corona(client, message, _):
    try:
        infected_amount, last_infected_date, recovered_amount, deaths_amount = await get_corona_stats()
        mortality_rate = deaths_amount / infected_amount

        percentage_of_people_to_get_infected = 40
        total_infections_over_time = POPULATION_OF_FINLAND * (percentage_of_people_to_get_infected / 100)
        total_deaths_over_time = round(total_infections_over_time * mortality_rate)
        await message.channel.send("\n".join([
            "**Corona statistics of Finland**",
            "**Total infected**: {0}".format(infected_amount),
            "**Total recovered:** {0}".format(recovered_amount),
            "**Total deaths:** {0}".format(deaths_amount),
            "**Mortality rate:** {0:.2f}%".format(mortality_rate * 100),
            "**Deaths if {0:.2f}% of population get infected:** {1}".format(percentage_of_people_to_get_infected, total_deaths_over_time),
            "**Last infection case:** {0}".format(last_infected_date.strftime('%Y-%m-%d %H:%M')),
        ]))
    except:
        await message.channel.send("There was an error getting corona stats.")


def register(client):
    return {
        "corona": cmd_corona
    }