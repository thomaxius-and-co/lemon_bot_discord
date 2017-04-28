# Anssi's first command!!
import time
import random
import asyncio

default_choices =["Kyllä", "Ei", "Ehkä"]
is_choices =["On", "Ei ole" , "Ehkä"]
where_choices =["Koska perseestä tulee paskaa", "Koska maailma ei ole valmis", "Koska botti on rikki"]
when_choices =["Viimeksi joulukuussa" , "Sitten kun anps voi hyvin" , "Ei vittu ikinä"]

async def cmd_ask(client, message, question):
    if not question:
        await client.send_message(message.channel, 'kys pls')
        return
    if question.lower().startswith("onko"):
        choices = is_choices
    elif question.lower().startswith("mistä"):
        choices = where_choices
    elif question.lower().startswith("milloin"):
        choices = when_choices
    else:
        choices = default_choices        
    await asyncio.sleep(2)
    await client.send_message(message.channel, random.choice(choices) + " :thinking: ")

def register(client):
    return {
        'ask': cmd_ask
    }
