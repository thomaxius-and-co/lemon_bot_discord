import discord
import re
import json
import database as db
import random as rand

playinglist = []

def sanitize_message(content, mentions):
    for m in mentions:
        content = content.replace("<@%s>" % m["id"], "@%s" % m["username"])
    return content

async def send_quote(client, channel, random_message):
    content, timestamp, mentions, author = random_message
    mentions = json.loads(mentions)
    author = json.loads(author)
    sanitized = sanitize_message(content, mentions)
    avatar_url = "https://cdn.discordapp.com/avatars/{id}/{avatar}.jpg".format(**author)

    embed = discord.Embed(description=sanitized)
    embed.set_author(name=author["username"], icon_url=avatar_url)
    embed.set_footer(text=str(timestamp))
    await client.send_message(channel, embed=embed)

async def random_message_with_filter(filters, params):
    async with db.connect() as c:
        return await c.fetchrow("""
            SELECT
                content,
                ts::timestamptz AT TIME ZONE 'Europe/Helsinki',
                m->'mentions',
                m->'author'
            FROM message
            WHERE length(content) > 6 AND content NOT LIKE '!%%' AND m->'author'->>'bot' IS NULL {filters}
            ORDER BY random()
            LIMIT 1
        """.format(filters=filters), *params)

async def getquoteforquotegame(name):
    async with db.connect() as c:
        for properquote in range(0,6):
            quote = await c.fetchrow("""
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
            if checkifproperquote(quote) > 6:
                return quote

def checkifproperquote(quote):
    return len(set(quote))

def make_word_filters(words):
    conditions = "content ~* $1"
    params = ["|".join(words)]
    return conditions, params

curses = [ "paska", "vittu", "vitu", "kusipää", "rotta", "saatana", "helvet", "kyrpä", "haista", "sossupummi" ]

async def random(filter):
    word_filters, params = make_word_filters(filter)
    return await random_message_with_filter("AND ({0})".format(word_filters), params)

async def random_quote_from_channel(channel_id):
    return await random_message_with_filter("AND m->>'channel_id' = $1", [channel_id])

async def get_user_days_in_chat(c):
    rows = await c.fetch("""
        SELECT
            m->'author'->>'id',
            extract(epoch from current_timestamp - min(ts)) / 60 / 60 / 24
        FROM message
        GROUP BY m->'author'->>'id'
    """)
    result = {}
    for row in rows:
        result[row[0]] = row[1]
# {'244610064038625280': 100.575020288113, '97767102722609152': 384.679490554317 }
    return result

async def top_message_counts(filters, params, excludecommands):
    sql_excludecommands = "AND content NOT LIKE '!%%'" if excludecommands else ""

    async with db.connect() as c:
        user_days_in_chat = await get_user_days_in_chat(c)
        items = await c.fetch("""
            select
                m->'author'->>'username' as name,
                m->'author'->>'id' as user_id,
                count(*) as messages
            from message
            WHERE m->'author'->>'bot' is null {sql_excludecommands} {filters}
            group by m->'author'->>'username', m->'author'->>'id'
        """.format(filters=filters, sql_excludecommands=sql_excludecommands), params)
        if len(items) <= 1:
            return None
        list_with_msg_per_day = []
        for item in items:
            name, user_id, message_count = item
            msg_per_day = message_count / user_days_in_chat[user_id]
            new_item = (name, msg_per_day, message_count)
            list_with_msg_per_day.append(new_item)
        top_ten = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:10]
        return fixlist(top_ten)

async def gettoplistforquotegame():
    async with db.connect() as c:
        items = await c.fetch("""
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
        if len(items) <= 1:
            return None
        toplist = []
        for item in items:
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

def fixlist1(sequence): # i am lazy today
    rank = 1
    namelen = column_width(sequence, 0, 9)
    maxnumberlen = column_width(sequence, 2, 6)
    print(sequence)
    for item in sequence:
        if (namelen >= len(item[0]) or (maxnumberlen >= len(str(item[1])))):
            fixed = item[0].ljust(namelen+1).ljust(namelen+2,'|')
            fixedtotal = str(item[2]).ljust(maxnumberlen)
            therank, thetotal, thecorrect = str(rank), str(item[2]), str(item[1])
            newitem = ('%s  #%s | %s| %s| %s' % (fixed,therank.ljust(2), fixedtotal, thecorrect.ljust(8),round(item[3],3)))
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

    excludecommands = input[0] != '!'

    input = input.lower()
    if input == ('spammers') or input == ('!spammers'):
        reply = await top_message_counts("AND 1 = $1", [1], excludecommands)
        if not reply:
            await client.send_message(message.channel,
                                      'Not enough chat logged into the database to form a toplist.')
            return

        parameter = '(commands included)' if not excludecommands else '(commands not included)'

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

        word = 'word' if len(customwords) == 1 else 'words'
        parameter = '(commands not included)' if excludecommands else '(commands included)'

        title = 'Top %s users of the %s: %s %s' % (len(reply), word, ', '.join(customwords), parameter)

        await client.send_message(message.channel, ('```%s \n NAME     | RANK | TOTAL | MSG PER DAY\n' % title + ('\n'.join(reply) + '```')))
        return

    if input == ('whosaidit'):
        ranking = await getwhosaiditranking()
        if not ranking:
            await client.send_message(message.channel,
                                      'Not enough players to form a toplist.')
            return

        title = 'Top %s players of !whosaidit (need 20 games to qualify):' % (len(ranking))
        await client.send_message(message.channel,
                                  ('```%s \n NAME     | RANK | TOTAL | CORRECT | ACCURACY %%\n' % title + ('\n'.join(ranking) + '```')))
        return
    else:
        await client.send_message(message.channel, 'Unknown list. Available lists: spammers, whosaidit, custom <words separated by comma>')
        return

async def getwhosaiditranking():
    async with db.connect(readonly = True) as c:
        items = await c.fetch("""
            SELECT
                (correct / (correct + wrong)) * 100,
                correct,
                correct + wrong,
                name
            FROM whosaidit_stats
            JOIN discord_user USING (user_id)
            WHERE (correct + wrong) > 19
            ORDER BY (correct / (correct + wrong)) * 100 DESC
            LIMIT 10
        """)
        if len(items) == 0:
            return None
        toplist = []
        for item in items:
            pct, correct, total, name = item
            new_item = (name, correct, total, pct)
            toplist.append(new_item)
        return fixlist1(toplist)

def filterquietpeople(tuple):
    return tuple[1] > 500
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
                                  '%s: Cannot play: You already have an unfinished game.' % message.author.name)
        return
    await dowhosaidit(client, message, _)

async def dowhosaidit(client, message, _):
    channel = message.channel
    topten = await gettoplistforquotegame()
    if not topten or len(topten) < 5:
        await client.send_message(channel,
                                  'Not enough chat logged to play.')
        playinglist.remove(message.author)
        return
    rand.shuffle(topten)
    name = rand.choice(topten)
    topten.remove(name)
    quote = await getquoteforquotegame(name)
    if not quote:
        await client.send_message(channel,
                                  'Not enough chat logged to play.') # I guess this is a pretty
        #  rare occasion, # but just in case
        playinglist.remove(message.author)
        return
    await send_question(client, message, topten, quote)

async def send_question(client, message, topten, thequote):
    name = thequote[1]
    sanitized = sanitize_message(thequote[0], json.loads(thequote[2]))
    options = [topten[0].lower(), topten[1].lower(), topten[2].lower(), topten[3].lower(),
               name.lower()]
    rand.shuffle(options)
    await client.send_message(message.channel,
                    "It's time to play 'Who said it?' !\n %s, who"
                    " said the following:\n ""*%s*""\n Options: %s. You have 15 seconds to answer!"
                              % (message.author.name, sanitized, ', '.join(options)))

    answer = await getresponse(client, name, options, message)
    if answer == 'correct':
        await client.send_message(message.channel, "%s: Correct! It was %s" % (message.author.name, name))
    elif answer == 'wrong':
        await client.send_message(message.channel, "%s: Wrong! It was %s" % (message.author.name, name))
    else:
        await client.send_message(message.channel, "%s: Time is up! The answer was %s" % (message.author.name, name))
    await save_stats(message.author.id, answer=answer)
    playinglist.remove(message.author)
    return

async def getresponse(client, name, options, message):
    def is_response(message):
        return message.content.lower() == name.lower() or message.content.lower() in options

    answer = await client.wait_for_message(timeout=15, channel=message.channel, author=message.author, check=is_response)
    if answer:
        if answer.content.lower() == name.lower():
            return 'correct'
        return 'wrong'

async def save_stats(userid, answer=None):
    if answer == 'correct':
        async with db.connect() as c:
            await c.execute("""
                INSERT INTO whosaidit_stats AS a
                (user_id, correct)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE
                SET correct = GREATEST(0, a.correct + EXCLUDED.correct)
            """, userid)
    else:
        async with db.connect() as c:
            await c.execute("""
                INSERT INTO whosaidit_stats AS a
                (user_id, wrong)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE
                SET wrong = GREATEST(0, a.wrong + EXCLUDED.wrong)
            """, userid)

def register(client):
    return {
        'randomquote': cmd_randomquote,
        'randomcurse': cmd_randomcurse,
        'whosaidit': cmd_whosaidit,
        'top': cmd_top
    }
