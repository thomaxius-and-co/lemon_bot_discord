import aiohttp
import asyncio

async def cmd_faceit_stats(client, message, faceit_nickname):
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname to search for.")
        return
    csgo_elo, csco_elo, skill_level, csgo_name = await get_stats_from_api(client, message, faceit_nickname)
    await client.send_message(message.channel, "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**CS:GO Elo**: %s\n**CS:CO Elo**: %s\n**Skill level**: %s" % (faceit_nickname, csgo_name, csgo_elo, csco_elo, skill_level))

async def get_stats_from_api(client, message, faceit_nickname):
    url = "https://api.faceit.com/api/nicknames/" + faceit_nickname
    async with aiohttp.ClientSession() as session:
        result = await session.get(url)
        result = await result.json()
        if result['result'] == 'error':
            await client.send_message(message.channel, "No stats for such nickname, or something else is wrong.")
            return
        csgo_name = result['payload']['csgo_name']
        skill_level = str(result['payload']['games']['csgo']['skill_level'])
        csgo_elo = str(result['payload']['games']['csgo']['faceit_elo'])
        csco_elo = str(result['payload']['games']['csco']['faceit_elo'])
        return csgo_elo, csco_elo, skill_level, csgo_name

def register(client):
    return {
        'faceitstats': cmd_faceit_stats
    }
