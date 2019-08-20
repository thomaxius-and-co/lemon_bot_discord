import database as db
import discord
from asyncio import sleep
import logger
from util import pmap
from time_util import as_utc

log = logger.get("emojicommands")

#todo: Add some sort of calculation of how many times certain emoji has been used per day since# it was added, mainly to give a more accurate 'popularity' ranking.

async def doemojilist(client, message):
    emojilist = []
    animated_emojilist = []
    x = 1
    for emoji in message.channel.guild.emojis:
        if emoji:
            rankandemoji = str(x) + ': ' + str(emoji)
            emojiname = ' :' + emoji.name + ': '
            created_at = emoji.created_at.date()  # Waiting for brother Henry to implement converttoguildtimezone(time)
            if emoji.url[-4:] == ".gif":
                animated_emojilist.append((rankandemoji, emojiname, str(created_at) + '\n'))
            else:
                emojilist.append((rankandemoji, emojiname, str(created_at)+'\n'))
            x += 1
    if not emojilist and not animated_emojilist:
        await message.channel.send('No emoji found.')
        return
    else:
        msg = ''
        i = 0
        for list in emojilist, animated_emojilist:
            i += 1
            if i == 2 and animated_emojilist:
                msg = "**Animated emojis:** \n"
            for item in list:
                if (len(msg) + len(''.join(map(''.join, item)))) > 1982:
                    await message.channel.send(msg)
                    msg = ''
                msg += ''.join(map(''.join, item))
                if item == list[-1]:
                    await message.channel.send(msg)

async def get_emojis(guild):
    return [x for x in guild.emojis if (x.url[-4:] != ".gif")]

async def get_animated_emojis(guild):
    return [x for x in guild.emojis if (x.url[-4:] != ".png")]

async def get_least_used_emojis(emojilist, guild_id):
    emojiswithusage = []
    for emoji in emojilist:
        result = await db.fetch("""
        SELECT 
            count(*) as count,
            extract(epoch from current_timestamp - $1) / 60 / 60 / 24 as daystocreated
        FROM 
            message 
        WHERE 
            content ~ $2 AND NOT bot AND guild_id = $3"""
        , as_utc(emoji.created_at), str(emoji), guild_id)
        if result:
            for item in result:
                count = item['count']
                used_per_day = count / item['daystocreated']
                emojiswithusage.append((str(emoji), count, round(used_per_day,3)))
    if not emojiswithusage:
        return None
    least_used_top_twentyfive = sorted(emojiswithusage, key=lambda x: x[2])[:25]
    return least_used_top_twentyfive

async def get_most_used_emojis(emojilist, guild_id):
    emojiswithusage = []
    for emoji in emojilist:
        result = await db.fetch("""
        SELECT 
            count(*) as count,
            extract(epoch from current_timestamp - $1) / 60 / 60 / 24 as daystocreated
        FROM 
            message 
        WHERE 
            content ~ $2 AND NOT bot AND guild_id = $3"""
        , as_utc(emoji.created_at), str(emoji), guild_id)
        if result:
            for item in result:
                count = item['count']
                used_per_day = count / item['daystocreated']
                emojiswithusage.append((str(emoji), count, round(used_per_day,3)))
    if not emojiswithusage:
        return None
    most_used_top_twentyfive = sorted(emojiswithusage, key=lambda x: x[2], reverse=True)[:25]
    return most_used_top_twentyfive

async def showleastusedemojis(client, message):
    animated_emojilist = await get_animated_emojis(message.channel.guild)
    emojilist = await get_emojis(message.channel.guild)
    if not emojilist and not animated_emojilist:
        await message.channel.send('No emoji found.')
        return
    top_twentyfive = await get_least_used_emojis(emojilist, message.channel.guild.id)
    top_twentyfive_animated = await get_least_used_emojis(animated_emojilist, message.channel.guild.id)
    if not top_twentyfive and not top_twentyfive_animated:
        await message.channel.send('No emoji has been used.')
        return
    if top_twentyfive:
        msg = ('Top 25 least used emoji :'
               '\n' + '\n'.join(
            map(''.join, [(x[0].ljust(3), ',' + str(x[1]).rjust(3), ', ' + str(x[2]).rjust(3)) for x in top_twentyfive]))
               + '\n(emoji, number of times used, times used per day)')
        await message.channel.send(msg[:1999])

    await sleep(.25)
    if top_twentyfive_animated:
        msg = ('Top 25 least used emoji (animated):'
               '\n' + '\n'.join(map(''.join,
                                    [(x[0].ljust(3), ',' + str(x[1]).rjust(3), ', ' + str(x[2]).rjust(3)) for x in
                                     top_twentyfive_animated]))
               + '\n(emoji, number of times used, times used per day)')
        await message.channel.send(msg[:1999])

async def showmostusedemojis(client, message):
    animated_emojilist = await get_animated_emojis(message.channel.guild)
    emojilist = await get_emojis(message.channel.guild)
    if not emojilist and not animated_emojilist:
        await message.channel.send('No emoji found.')
        return
    top_twentyfive = await get_most_used_emojis(emojilist, message.channel.guild.id)
    top_twentyfive_animated = await get_most_used_emojis(animated_emojilist, message.channel.guild.id)

    if not top_twentyfive and not top_twentyfive_animated:
        await message.channel.send('No emoji has been used.')
        return
    if top_twentyfive:
        msg = ('Top 25 most used emoji :'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3), ', ' + str(x[2]).rjust(3)) for x in top_twentyfive]))
                              + '\n(emoji, number of times used, times used per day)')
        await message.channel.send(msg[:1999])

    await sleep(.25)
    if top_twentyfive_animated:
        msg = ('Top 25 most used emoji (animated):'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3), ', ' + str(x[2]).rjust(3)) for x in top_twentyfive_animated]))
                              + '\n(emoji, number of times used, times used per day)')
        await message.channel.send(msg[:1999])

async def cmd_emojicommands(client, message, arg):
    if arg.lower() == 'leastused':
        await showleastusedemojis(client, message)
        return
    if arg.lower() == 'mostused':
        await showmostusedemojis(client, message)
        return
    if arg.lower() == 'list':
        await doemojilist(client, message)
    else:
        await message.channel.send('Usage: !emoji <list> or <leastused> or <mostused>')  # obv more features will be added later
        return

def register(client):
    return {
        'emoji': cmd_emojicommands,
    }
