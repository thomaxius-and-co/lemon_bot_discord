import urllib
import aiohttp
from bs4 import BeautifulSoup

def register(client):
    return {
        "youtube": cmd_youtube,
        "yt": cmd_youtube,
    }

async def cmd_youtube(client, message, query):
    query = urllib.parse.quote(query)
    search_url = "https://www.youtube.com/results?search_query=" + query
    async with aiohttp.ClientSession() as session:
        r = await session.get(search_url)
        html = BeautifulSoup(await r.text(), "lxml")
        element = html.find(attrs={'class': 'yt-uix-tile-link'})
        if element is None:
            await message.channel.send("Sorry, I couldn't find any videos with that query.")
            return

        url = 'https://www.youtube.com' + element['href']
        await message.channel.send(url)

