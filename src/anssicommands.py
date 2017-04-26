# Anssi's first command!!

import random
import time
import discord

choices=["Todellakin\n","Kyllä\n","Varmaan\n","Ehkä\n","Todennäköisesti ei\n","Ei\n","Ei todellakaan\n","En tiedä\n","Kysy myöhemmin\n","Eipä ollu\n"]


async def cmd_ask(client, message, _):
    while True:
        for i in range(0,2):
            await client.send_message(message.channel, " :thinking: \n")
            time.sleep(1)
        await client.send_message(message.channel, random.choice(choices))
        break

def register(client):
    return {
        'ask': cmd_ask
    }