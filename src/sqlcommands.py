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

async def random_message_with_filter(filters, params):
    async with db.connect(readonly = True) as c:
        await c.execute("""
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
        return await c.fetchone()

def make_word_filters(words):
    conditions = " OR ".join(["content ILIKE %s"] * len(words))
    params = list(map("%{0}%".format, words))
    return conditions, params

curses = [ "paska", "vittu", "vitu", "kusipää", "rotta", "saatana", "helvet", "kyrpä", "haista", "sossupummi" ]
hatewords = [ "nigga", "negro", "manne", "mustalainen", "rättipää", "ryssä", "vinosilmä", "jutku", "neeke" ]



async def random(filter):
    word_filters, params = make_word_filters(filter)
    return await random_message_with_filter("AND ({0})".format(word_filters), params)

async def random_quote_from_channel(channel_id):
    return await random_message_with_filter("AND m->>'channel_id' = %s", [channel_id])

async def top_message_counts(title, filters, params):
    async with db.connect(readonly = True) as c:
        await c.execute("""
            with tmp as
                (select m->'author'->>'username' as name,
                count(*) / extract(epoch from current_timestamp - min((m->>'timestamp')::timestamptz)) * 60 * 60 * 24
                as msg_per_day,
                count(*) as messages
                from message
                WHERE content NOT LIKE '!%%' and m->'author'->>'bot' is null {filters}
                group by m->'author'->>'username')
            select * from tmp order by msg_per_day desc
            limit 10;
        """.format(filters=filters), params)
        if c.rowcount <= 1:
            return None
        nicequery = await fixlist(await c.fetchall())
        return nicequery

def check_length(x,i):
    return len(str(x[i]))

async def fixlist(sequence):
    maxnamelen = sequence[0]
    maxnumberlen = 6
    rank = 1
    for item in sequence:
        if check_length(item,0) > check_length(maxnamelen,0):
            maxnamelen = item
            namelen = len(maxnamelen[0])
        if check_length(item, 2) > maxnumberlen:
            maxnumberlen = len(str(item))

    for item in sequence:
        if (namelen >= len(item[0]) or (maxnumberlen >= len(str(item[1])))):
            fixed = item[0].ljust(namelen+1).ljust(namelen+2,'|')
            fixedtotal = str(item[2]).ljust(maxnumberlen)
            therank, thetotal = str(rank), str(item[2])
            newitem = ('%s  #%s | %s| %s' % (fixed,therank.ljust(2), fixedtotal,round(item[1],3)))
            rank += 1
            pos = sequence.index(item)
            sequence.remove(item)
            sequence.insert(pos,newitem)
    return sequence

async def cmd_top(client, message, input):
    if not input:
        await client.send_message(message.channel, 'You need to specify a toplist. Available toplists: spammers, racists')
        return

    input = input.lower()
    if input == 'spammers':
        reply = await top_message_counts(input, "AND 1 = %s", [1])
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return
        await client.send_message(message.channel, ('```Top %s spammers\n NAME     | RANK | TOTAL | MSG PER DAY\n' % len(reply) + ('\n'.join(reply) + '```')))
        return
    if input == 'racists':
        filters, params = make_word_filters(hatewords)
        racists_filter = "AND ({0})".format(filters)
        reply = await top_message_counts(input, racists_filter, params)
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return
        await client.send_message(message.channel, ('```Top %s racists\n NAME     | RANK | TOTAL | MSG PER DAY\n' % len(reply) + ('\n'.join(reply) + '```')))
    else:
        await client.send_message(message.channel, 'Unknown list. Availabe lists: spammers, racists ')
        return

async def cmd_randomquote(client, themessage, input):
    if input is not None and 'custom' in input.lower():
        channel = themessage.channel
        customwords = input.split(' ')
        if len(customwords) > 50:
            await client.send_message(channel, "Please broaden your query, max allowed words is 50.")
            return
        customwords.pop(0)
        random_message = await random(''.join(customwords).split(','))
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

    random_message = await random_quote_from_channel(channel.id)
    if random_message is None:
        await client.send_message(themessage.channel, "Sorry, no messages could be found")
    else:
        await send_quote(client, themessage.channel, random_message)

async def cmd_randomcurse(client, themessage, _):
    channel = themessage.channel
    random_message = await random(curses)
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
