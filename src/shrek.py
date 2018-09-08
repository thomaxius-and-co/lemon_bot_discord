from datetime import datetime

def register(client):
    return {
        "shrek": cmd_shrek
    }

async def cmd_shrek(client, message, arg):
        try:
            birthyear = datetime.strptime(arg, "%d.%m.%Y")
        except:
            await client.send_message(message.channel,
                                      "Usage: !shrek <your birthdate as dd.mm.yyyy> for example, !shrek 29.04.1993")
            return
        now = datetime.now()
        difference = abs(now - birthyear).days * 1440
        age_in_shreks = difference / 95
        await client.send_message(message.channel, "You are %s shreks old." % round(age_in_shreks, 2))
