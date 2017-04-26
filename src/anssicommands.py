# Anssi's first command!!
import time
import random
import asyncio

choices=["Todellakin","Kyllä","Lopeta heti kyseleminen","Ehkä","Todennäköisesti ei","Ei","Ei todellakaan","En tiedä","Juuh joo","Juuh ei","Varmasti","Lol ei"]

async def cmd_ask(client, message, _):
    await client.send_message(message.channel, " :thinking: ")
    await asyncio.sleep(2)
    await client.send_message(message.channel, random.choice(choices))

def register(client):
    return {
        'ask': cmd_ask
    }
