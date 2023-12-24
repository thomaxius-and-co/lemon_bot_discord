from datetime import datetime

def register():
    return {
        "shrek": cmd_shrek
    }

async def cmd_shrek(client, message, arg):
        try:
            birthyear = datetime.strptime(arg, "%d.%m.%Y")
        except:
            await message.channel.send("Usage: !shrek <your birthdate as dd.mm.yyyy> for example, !shrek 29.04.1993")
            return
        now = datetime.now()
        difference = abs(now - birthyear).days * 1440
        age_in_shreks = difference / 95
        if birthyear > now:
            await message.channel.send("Your baby will be born in %s shreks." % round(age_in_shreks, 2))
        else:
            await message.channel.send("You are %s shreks old." % round(age_in_shreks, 2))
