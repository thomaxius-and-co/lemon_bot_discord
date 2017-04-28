# Anssi's first command!!
import time
import random
import asyncio

default_choices =["Kyllä", "Ei", "Ehkä"]
is_choices =["On", "Ei ole" , "Ehkä"]
from_choices =["Pyllystä", "Sun mutsista", "Sossusta", "Kaupasta", "No vittu just sieltä", "Säkylästä"]
when_choices =["Viimeksi joulukuussa" , "Sitten kun anps voi hyvin" , "Ei vittu ikinä"]
why_choices =["Koska säkylän pystykorvat" , "Kukaan ei tiedä" , "Se on jumalan suunnitelma"]
where_choices =["Helvetin perseessä" , "Jumalan selän takana" , "Nyrkki perseessä thaimaassa"]

async def cmd_ask(client, message, question):
    if not question:
        await client.send_message(message.channel, 'kys pls')
        return

    if question.lower().startswith("onko"):
        choices = is_choices
    elif question.lower().startswith("mistä"):
        choices = from_choices
    elif question.lower().startswith("milloin"):
        choices = when_choices
    elif question.lower().startswith("miksi") or question.lower().startswith("minkä takia"):
        choices = why_choices
    elif question.lower().startswith("missä"):
        choices = where_choices
    else:
        choices = default_choices

    await asyncio.sleep(2)
    await client.send_message(message.channel, random.choice(choices) + " :thinking: ")

def register(client):
    return {
        'ask': cmd_ask
    }
