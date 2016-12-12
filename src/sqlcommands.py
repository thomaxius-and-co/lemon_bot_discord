import discord

import database as db

def sanitize_message(content, mentions):
    for m in mentions:
        content = content.replace("<@%s>" % m["id"], "@%s" % m["username"])
    return content

async def send_quote(client, channel, random_message):
    content, timestamp, mentions, author = random_message
    sanitized = sanitize_message(content, mentions)
    avatar_url = "https://cdn.discordapp.com/avatars/{id}/{avatar}.jpg".format(**author)

    embed = discord.Embed(description=sanitized)
    embed.set_author(name=author["username"], icon_url=avatar_url)
    embed.set_footer(text=str(timestamp))
    await client.send_message(channel, embed=embed)

def random_message_with_filter(filters, params):
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT
                content,
                ts::timestamptz AT TIME ZONE 'Europe/Helsinki',
                m->'mentions',
                m->'author'
            FROM message
            WHERE length(content) > 6 AND content NOT LIKE '!%%' AND m->'author'->>'bot' IS NULL {filters}
            ORDER BY random()
            LIMIT 1
        """.format(filters=filters), params)
        return c.fetchone()

def make_word_filters(words):
    conditions = " OR ".join(["lower(content) LIKE %s"] * len(words))
    params = list(map("%{0}%".format, words))
    return conditions, params

curses = [ "paska", "vittu", "vitu", "kusipää", "rotta", "saatana", "helvet", "kyrpä", "haista", "sossupummi" ]
hatewords = [ "nigga", "negro", "manne", "mustalainen", "rättipää", "ryssä", "vinosilmä", "jutku", "neeke" ]



def random(filter):
    word_filters, params = make_word_filters(filter)
    return random_message_with_filter("AND ({0})".format(word_filters), params)

def random_quote_from_channel(channel_id):
    return random_message_with_filter("AND m->>'channel_id' = %s", [channel_id])

def top_message_counts(filters=""):
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT m->'author'->>'username' AS User, count(*) as messages
            FROM message
            WHERE  lower(content) NOT LIKE '!%' and m->'author'->>'bot' is null {filters}
            GROUP BY m->'author'->>'username'
            ORDER BY count(*) DESC
            limit 10;
        """.format(filters=filters))
        nicequery = makequerynice(c.fetchall(),title='racists')
        return nicequery

def makequerynice(uglyquery, title):
    i = 0
    l = uglyquery
    l1 = []
    for x in uglyquery:
        reply = '**%s**, %s messages' % (l[i][0], l[i][1])
        l1.append(reply)
        i += 1
    reply = ('Top 10 %s:\n'
                                     '1: %s\n2: %s\n3: %s\n4: %s\n5: %s\n6: %s\n'
                                     '7: %s\n8: %s\n9: %s\n10: %s' %
                    (title, l1[0], l1[1], l1[2], l1[3], l1[4], l1[5], l1[6],
                     l1[7], l1[8], l1[9]))
    return reply

async def cmd_top(client, message, input):
    input = input.lower()
    if not input:
        await client.send_message(message.channel, 'You need to specify a toplist. Available toplists: spammers, racists')
        return
    if input == 'spammers':
        reply = top_message_counts()
        await client.send_message(message.channel, reply)
        return
    if input == 'racists':
        racists_filter = "AND ({0})".format(make_word_filters(hatewords))
        reply = top_message_counts(racists_filter)
        await client.send_message(message.channel, reply)
        return
    else:
        await client.send_message(message.channel, 'Unknown list. Availabe lists: spammers, racists ')
        return

async def cmd_randomquote(client, themessage, input):
    if 'custom' in input.lower():
        channel = themessage.channel
        customwords = input.split(' ')
        customwords.remove('custom')
        customwords = ''.join(customwords)
        random_message = random(customwords.split(','))
        if random_message is None:
            await client.send_message(channel, "Sorry, no messages could be found")
            return
        await send_quote(client, channel, random_message)
        return
    channel = None
    if input is None:
        channel = themessage.channel
    else:
        server = themessage.channel.server
        for c in server.channels:
            if c.name == input:
                channel = c
                break

        if channel is None:
            await client.send_message(themessage.channel, "Sorry, I couldn't find such channel")
            return

    random_message = random_quote_from_channel(channel.id)
    if random_message is None:
        await client.send_message(themessage.channel, "Sorry, no messages could be found")
    else:
        await send_quote(client, themessage.channel, random_message)

async def cmd_randomcurse(client, themessage, _):
    channel = themessage.channel
    random_message = random(curses)
    if random_message is None:
        await client.send_message(channel, "Sorry, no messages could be found")
    else:
        await send_quote(client, channel, random_message)

def register(client):
    return {
        'randomquote': cmd_randomquote,
        'randomcurse': cmd_randomcurse,
        'top': cmd_top
    }
