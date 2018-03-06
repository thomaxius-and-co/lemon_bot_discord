import database as db
import discord
from asyncio import sleep
import logger
from util import pmap

log = logger.get("emojicommands")

#todo: Add some sort of calculation of how many times certain emoji has been used per day since# it was added, mainly to give a more accurate 'popularity' ranking.

async def doemojilist(client, message):
    emojilist = []
    animated_emojilist = []
    x = 1
    for emoji in message.channel.server.emojis:
        if emoji:
            rankandemoji = str(x) + ': ' + str(emoji)
            emojiname = ' :' + emoji.name + ': '
            created_at = emoji.created_at.date()  # Waiting for brother Henry to implement converttoguildtimezone(time)
            log.info(emoji.url, "Emoji url")
            if emoji.url[-4:] == ".gif":
                animated_emojilist.append((rankandemoji, emojiname, str(created_at) + '\n'))
            else:
                emojilist.append((rankandemoji, emojiname, str(created_at)+'\n'))
            x += 1
    if not emojilist and not animated_emojilist:
        await client.send_message(message.channel, 'No emoji found.')
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
                    await client.send_message(message.channel, msg)
                    msg = ''
                msg += ''.join(map(''.join, item))
                if item == list[-1]:
                    await client.send_message(message.channel, msg)

async def get_emojis(server):
    return [str(x) for x in server.emojis if (x.url[-4:] != ".gif")]

async def get_animated_emojis(server):
    return [str(x) for x in server.emojis if (x.url[-4:] != ".png")]

async def get_least_used_emojis(emojilist, server_id):
    emojiswithusage = []
    for emoji in emojilist:
        count = await db.fetchval("select count(*) from message where content ~ $1 AND NOT bot AND guild_id = $2", emoji, server_id)
        emojiswithusage.append((emoji, count))
    if not emojiswithusage:
        return None
    least_used_top_twentyfive = sorted(emojiswithusage, key=lambda x: x[1])[:25]
    return least_used_top_twentyfive

async def get_most_used_emojis(emojilist, server_id):
    emojiswithusage = []
    for emoji in emojilist:
        count = await db.fetchval("select count(*) from message where content ~ $1 AND NOT bot AND guild_id = $2", emoji, server_id)
        if count:
            emojiswithusage.append((emoji, count))
    if not emojiswithusage:
        return None
    most_used_top_twentyfive = sorted(emojiswithusage, key=lambda x: x[1], reverse=True)[:25]
    return most_used_top_twentyfive

async def showleastusedemojis(client, message):
    animated_emojilist = await get_animated_emojis(message.channel.server)
    emojilist = await get_emojis(message.channel.server)
    if not emojilist and not animated_emojilist:
        await client.send_message(message.channel, 'No emoji found.')
        return
    top_twentyfive = await get_least_used_emojis(emojilist, message.channel.server.id)
    top_twentyfive_animated = await get_least_used_emojis(animated_emojilist, message.channel.server.id)
    if not top_twentyfive and not top_twentyfive_animated:
        await client.send_message(message.channel, 'No emoji has been used.')
        return
    if top_twentyfive:
        await client.send_message(message.channel, 'Top 25 least used emoji:'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3)) for x in top_twentyfive ]))
                              + '\n(emoji, number of times used)')
    if top_twentyfive_animated:
        await client.send_message(message.channel, 'Top 25 least used emoji (animated):'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3)) for x in top_twentyfive_animated ]))
                              + '\n(emoji, number of times used)')

async def showmostusedemojis(client, message):
    animated_emojilist = await get_animated_emojis(message.channel.server)
    emojilist = await get_emojis(message.channel.server)
    if not emojilist and not animated_emojilist:
        await client.send_message(message.channel, 'No emoji found.')
        return
    top_twentyfive = await get_most_used_emojis(emojilist, message.channel.server.id)
    top_twentyfive_animated = await get_most_used_emojis(animated_emojilist, message.channel.server.id)
    if not top_twentyfive and not top_twentyfive_animated:
        await client.send_message(message.channel, 'No emoji has been used.')
        return
    if top_twentyfive:
        await client.send_message(message.channel, 'Top 25 most used emoji:'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3)) for x in top_twentyfive ]))
                              + '\n(emoji, number of times used)')
    await sleep(.25)
    if top_twentyfive_animated:
        await client.send_message(message.channel, 'Top 25 most used emoji (animated):'
                                               '\n'+'\n'.join(map(''.join, [ (x[0].ljust(3), ',' + str(x[1]).rjust(3)) for x in top_twentyfive_animated ]))
                              + '\n(emoji, number of times used)')

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
        await client.send_message(message.channel, 'Usage: !emoji <list> or <leastused> or <mostused>')  # obv more features will be added later
        return

def register(client):
    return {
        'emoji': cmd_emojicommands,
    }
