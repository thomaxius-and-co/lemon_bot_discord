import aiohttp
import asyncio

async def cmd_faceit_stats(client, message, faceit_nickname):
    if not faceit_nickname:
        await client.send_message(message.channel, "You need to specify a faceit nickname to search for.")
        return
    csgo_elo, skill_level, csgo_name, ranking_eu = await get_user_stats_from_api(client, message, faceit_nickname)
    await client.send_message(message.channel, "Faceit stats for player nicknamed **%s**:\n**Name**: %s\n**EU ranking**: %s\n**CS:GO Elo**: %s\n**Skill level**: %s" % (faceit_nickname, csgo_name,  ranking_eu, csgo_elo, skill_level))

async def get_user_stats_from_api(client, message, faceit_nickname):
    user_stats_url = "https://api.faceit.com/api/nicknames/" + faceit_nickname
    async with aiohttp.ClientSession() as session:
        result = await session.get(user_stats_url)
        result = await result.json()
        if result['result'] == 'error':
           await client.send_message(message.channel, result['message'].replace(result['message'][0],result['message'][0].upper()) + ".") #Yes, I am this triggered by the first letter being a non-capital
           return
        csgo_name = result.get("payload", {}).get("csgo_name", "-")
        skill_level = result.get("payload", {}).get("games", {}).get("csgo", {}).get("skill_level", "-")
        csgo_elo = result.get("payload", {}).get("games", {}).get("csgo", {}).get("faceit_elo", "-")
        ranking = await get_user_eu_ranking(result.get("payload", {}).get("guid", {})) if csgo_elo != "-" else "-"
        return str(csgo_elo), str(skill_level), csgo_name, ranking

async def get_user_eu_ranking(faceit_guid):
    eu_ranking_url = "https://api.faceit.com/ranking/v1/globalranking/csgo/EU/" + faceit_guid
    async with aiohttp.ClientSession() as session:
        result = await session.get(eu_ranking_url)
        result = await result.json()
        return str(result.get("payload", "-"))

def register(client):
    return {
        'faceitstats': cmd_faceit_stats
    }
