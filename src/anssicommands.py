# Anssi's first command!!
import time
import random
import asyncio

choices=["Todennäköisesti kyllä","Kyllä","Ei","Todennäköisesti ei","Ei todellakaan","En tiedä","Jooh","Juuh ei","Varmasti","Lol ei"]

async def cmd_ask(client, message, _):
    await client.send_message(message.channel)
    await asyncio.sleep(2)
    await client.send_message(message.channel, random.choice(choices) + " :thinking: ")

def register(client):
    return {
        'ask': cmd_ask
    }
