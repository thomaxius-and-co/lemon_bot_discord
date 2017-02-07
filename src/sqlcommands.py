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
    conditions = "content ~* %s"
    params = ["|".join(words)]
    return conditions, params

curses = [ "paska", "vittu", "vitu", "kusipää", "rotta", "saatana", "helvet", "kyrpä", "haista", "sossupummi" ]

async def random(filter):
    word_filters, params = make_word_filters(filter)
    return await random_message_with_filter("AND ({0})".format(word_filters), params)

async def random_quote_from_channel(channel_id):
    return await random_message_with_filter("AND m->>'channel_id' = %s", [channel_id])

async def get_user_days_in_chat(c):
    await c.execute("""
        SELECT
            m->'author'->>'id',
            extract(epoch from current_timestamp - min(ts)) / 60 / 60 / 24
        FROM message
        GROUP BY m->'author'->>'id'
    """)
    result = {}
    for row in (await c.fetchall()):
        result[row[0]] = row[1]
    return result

async def top_message_counts(title, filters, params):
    async with db.connect(readonly = True) as c:
        user_days_in_chat = await get_user_days_in_chat(c)

        await c.execute("""
            select
                m->'author'->>'username' as name,
                m->'author'->>'id' as user_id,
                count(*) as messages
            from message
            WHERE content NOT LIKE '!%%' and m->'author'->>'bot' is null {filters}
            group by m->'author'->>'username', m->'author'->>'id'
        """.format(filters=filters), params)
        if c.rowcount <= 1:
            return None
        list_with_msg_per_day = []
        for item in await c.fetchall():
            name, user_id, message_count = item
            msg_per_day = message_count / user_days_in_chat[user_id]
            new_item = (name, msg_per_day, message_count)
            list_with_msg_per_day.append(new_item)
        top_ten = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:10]
        return fixlist(top_ten)

def check_length(x,i):
    return len(str(x[i]))

def column_width(tuples, index, min_width):
    widest = max([check_length(x, index) for x in tuples])
    return max(min_width, widest)

def fixlist(sequence):
    rank = 1
    namelen = column_width(sequence, 0, 9)
    maxnumberlen = column_width(sequence, 2, 6)

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
    # sequence: ['user1 |  #1  | 27    | 0.236', 'user2     |  #2  | 48    | and so forth
    return sequence

async def cmd_top(client, message, input):
    if not input:
        await client.send_message(message.channel, 'You need to specify a toplist. Available toplists: spammers,'
                                                   ' custom <words separated by comma>')
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

    if 'custom' in input[0:6]:
        customwords = await getcustomwords(input, message, client)
        if not customwords:
            return
        filters, params = make_word_filters(customwords)
        custom_filter = "AND ({0})".format(filters)
        reply = await top_message_counts(input, custom_filter, params)
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return
        if len(customwords) == 1:
            word = 'word'
        else:
            word = 'words'
        title = 'Top %s users of the %s: %s' % (len(reply), word,  ' '.join(customwords))

        await client.send_message(message.channel, ('```%s \n NAME     | RANK | TOTAL | MSG PER DAY\n' % title + ('\n'.join(reply) + '```')))
        return
    else:
        await client.send_message(message.channel, 'Unknown list. Availabe lists: spammers, custom <words separated by comma>')
        return

async def getcustomwords(input, message, client):

    customwords = input.split(' ')
    if len(customwords) == 1:
        await client.send_message(message.channel, "You need to specify custom words to search for.")
        return
    customwords.pop(0)
    customwords = ''.join(customwords).split(',')

    # Remove empty words from search, which occured when user typed a comma without text (!top custom test,)
    lowest = (min(customwords, key=len))
    while len((min(customwords, key=len))) == 0:
        customwords.remove(lowest)
    return customwords
async def cmd_randomquote(client, themessage, input):
    if input is not None and 'custom' in input.lower()[0:6]:
        channel = themessage.channel
        customwords = await getcustomwords(input, themessage, client)
        if not customwords:
            await client.send_message(channel, "You need to specify words to search for.")
            return
        random_message = await random(customwords)
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
