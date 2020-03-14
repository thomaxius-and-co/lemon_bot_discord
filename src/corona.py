import logger
import datetime
import aiohttp

log = logger.get("CORONA")

CORONA_API_URL = 'https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData'




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
        await message.channel.send("**Total infected**: {0}\n**Total recovered:** {1}\n**Total deaths:** {2}\n**Last infection case:** {3}"
                                   .format(infected_amount, recovered_amount, deaths_amount, last_infected_date.strftime('%Y-%m-%d %H:%M')))
    except:
        await message.channel.send("There was an error getting corona stats.")


def register(client):
    return {
        "corona": cmd_corona
    }