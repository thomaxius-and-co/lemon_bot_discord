import discord
import re
import database as db
import random as rand

playinglist = []

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

async def getquoteforquotegame(name):
    async with db.connect(readonly = True) as c:
        await c.execute("""
            SELECT
                content,
                m->'author'->>'username',
                m->'mentions'
            FROM message
            WHERE length(content) > 12 AND content NOT LIKE '!%%' AND content NOT LIKE '%wwww%'
             AND content NOT LIKE '%http%' AND content NOT LIKE '%.com%' AND content NOT LIKE '%.fi%'
             AND m->'author'->>'bot' IS NULL AND m->'author'->>'username' LIKE '{name}'
            ORDER BY random()
            LIMIT 1
        """.format(name=name))
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
# {'244610064038625280': 100.575020288113, '97767102722609152': 384.679490554317 }
    return result

async def top_message_counts(filters, params, excludecommands):
    async with db.connect(readonly = True) as c:
        user_days_in_chat = await get_user_days_in_chat(c)
        await c.execute("""
            select
                m->'author'->>'username' as name,
                m->'author'->>'id' as user_id,
                count(*) as messages
            from message
            WHERE m->'author'->>'bot' is null{excludecommands} {filters}
            group by m->'author'->>'username', m->'author'->>'id'
        """.format(filters=filters, excludecommands=excludecommands), params)
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

async def gettoplistforquotegame():
    async with db.connect(readonly = True) as c:
        await c.execute("""
            select
                m->'author'->>'username' as name,
                m->'author'->>'id' as user_id,
                count(*) as messages
            from message
            WHERE m->'author'->>'bot' is null and length(content) > 12 AND content NOT LIKE '!%%' AND content NOT LIKE '%wwww%'
             AND content NOT LIKE '%http%' AND content NOT LIKE '%.com%' AND content NOT LIKE '%.fi%'
             AND m->'author'->>'bot' IS NULL AND m->'author'->>'username' not like 'toxin'
            group by m->'author'->>'username', m->'author'->>'id'
        """)
        if c.rowcount <= 1:
            return None
        toplist = []
        for item in await c.fetchall():
            name, user_id, message_count = item
            new_item = (name, message_count)
            toplist.append(new_item)
        top_ten = sorted(toplist, key=lambda x: x[1], reverse=True)[:15]
        return [msgs[0] for msgs in top_ten if filterquietpeople(msgs)]

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
    excludecommands = " and content NOT LIKE '!%%'"
    if not input:
        await client.send_message(message.channel, 'You need to specify a toplist. Available toplists: spammers,'
                                                   ' custom <words separated by comma>')
        return
    if input[0] == '!':
        excludecommands = ""
    input = input.lower()

    if input == ('spammers') or input == ('!spammers'):
        reply = await top_message_counts("AND 1 = %s", [1], excludecommands)
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return
        if not excludecommands:
            parameter = '(commands included)'
        else:
            parameter = '(commands not included)'
        header = 'Top %s spammers %s \n NAME     | RANK | TOTAL | MSG PER DAY\n' % (len(reply), parameter)
        body = '\n'.join(reply)
        await client.send_message(message.channel, '``' + header + body + '``')
        return

    if input[0:6] == ('custom') or input[0:7] == ('!custom'):
        customwords = await getcustomwords(input, message, client)
        if not customwords:
            return
        filters, params = make_word_filters(customwords)
        custom_filter = "AND ({0})".format(filters)
        reply = await top_message_counts(custom_filter, params, excludecommands)
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return
        if len(customwords) == 1:
            word = 'word'
        else:
            word = 'words'
        if not excludecommands:
            parameter = '(commands included)'
        else:
            parameter = '(commands not included)'
        title = 'Top %s users of the %s: %s %s' % (len(reply), word, ', '.join(customwords), parameter)

        await client.send_message(message.channel, ('```%s \n NAME     | RANK | TOTAL | MSG PER DAY\n' % title + ('\n'.join(reply) + '```')))
        return
    else:
        await client.send_message(message.channel, 'Unknown list. Available lists: spammers, custom <words separated by comma>')
        return

def filterquietpeople(tuple):
    return tuple[1] > 1000

async def getcustomwords(input, message, client):
    # Remove empty words from search, which occured when user typed a comma without text (!top custom test,)
    customwords = list(map(lambda x: x.strip(), re.sub('!?custom', '', input).split(',')))
    def checkifsmall(value):
        return len(value) > 0
    customwords = [word for word in customwords if checkifsmall(word)]
    if len(customwords) == 0:
        await client.send_message(message.channel,"You need to specify custom words to search for.")
        return
    return customwords

async def cmd_randomquote(client, themessage, input):
    if input is not None and 'custom' in input.lower()[0:6]:
        channel = themessage.channel
        customwords = await getcustomwords(input, themessage, client)
        if not customwords:
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


async def cmd_whosaidit(client, message, _):
    if message.author not in playinglist:
        playinglist.append(message.author)
    else:
        await client.send_message(message.channel,
                                  '%s: Cannot play: You already have an unfinished game.' % message.author)
        return
    await dowhosaidit(client, message, _)

async def dowhosaidit(client, message, _):
    channel = message.channel
    topten = await gettoplistforquotegame()
    if len(topten) < 5:
        await client.send_message(channel,
                                  'Not enough chat logged to play')
        return
    rand.shuffle(topten)
    name = rand.choice(topten)
    topten.remove(name)
    quote = await getquoteforquotegame(name)
    await send_question(client, message, topten, quote)

async def send_question(client, message, topten, thequote):
    name = thequote[1]
    sanitized = sanitize_message(thequote[0], thequote[2])
    options = [topten[0].lower(), topten[1].lower(), topten[2].lower(), topten[3].lower(),
               name.lower()]
    rand.shuffle(options)
    await client.send_message(message.channel,
                    "It's time to play 'Who said it?' !\n %s, who"
                    " said the following:\n ""*%s*""\n Options: %s. You have 10 seconds to answer!"
                              % (message.author, sanitized, ', '.join(options)))
    while True:
        answer = await getresponse(client, name, options, message)
        if answer:
            if answer == 'correct':
                await client.send_message(message.channel, "%s: Correct! It was %s" % (message.author, name))
                break
            if answer == 'wrong':
                await client.send_message(message.channel, "%s: Wrong! It was %s" % (message.author, name))
                break
        if not answer:
            await client.send_message(message.channel, "%s: Time is up! The answer was %s" % (message.author, name))
            break
    playinglist.remove(message.author)
    return

def check(message):
    return message.author == message.author

async def getresponse(client, name, options, message):
    answer = await client.wait_for_message(timeout=10, author=message.author, check=check)
    if answer and answer.content.lower() == name.lower():
        answer = 'correct'
        return answer
    if answer and answer.content.lower() in options:
        answer = 'wrong'
        return answer
    if answer:
        return True
    else:
        return False


def register(client):
    return {
        'randomquote': cmd_randomquote,
        'randomcurse': cmd_randomcurse,
        'whosaidit': cmd_whosaidit,
        'top': cmd_top
    }
