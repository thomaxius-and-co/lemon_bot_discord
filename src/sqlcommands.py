import database as db

def sanitize_message(content, mentions):
    for m in mentions:
        content = content.replace("<@%s>" % m["id"], "@%s" % m["username"])
    return content

def random_message_with_filter(filters, params=None):
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT
                m->>'content',
                (m->>'timestamp')::timestamptz AT TIME ZONE 'Europe/Helsinki',
                m->'author'->>'username',
                m->'mentions'
            FROM message
            WHERE length(m->>'content') > 6 AND m->>'content' NOT LIKE '!%%' AND m->'author'->>'bot' IS NULL {filters}
            ORDER BY random()
            LIMIT 1
        """.format(filters=filters), params)
        return c.fetchone()

def make_word_filters(words):
    conditions = map("lower(m->>'content') LIKE '%{0}%'".format, words)
    return " OR ".join(conditions)

curses = [ "paska", "vittu", "vitu", "kusipää", "rotta", "saatana", "helvet", "kyrpä", "haista", "sossupummi" ]

def random_curse():
    word_filters = make_word_filters(curses)
    return random_message_with_filter("AND ({0})".format(word_filters))

def random_quote_from_channel(channel_id):
    return random_message_with_filter("AND m->>'channel_id' = %s", [channel_id])

def doquery():
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT m->'author'->>'username' AS User, count(*) as messages
            FROM message
            WHERE  lower(m->>'content') NOT LIKE '!%' and m->'author'->>'bot' is null
            GROUP BY m->'author'->>'username'
            ORDER BY count(*) DESC
            limit 10;
        """)
        return c.fetchall()

async def cmd_top(client, message, input):
    if input.lower() == 'spammers':
        l = doquery()
        i = 0
        l1 = []
        for x in l:
            reply = '**%s**, %s messages' % (l[i][0], l[i][1])
            l1.append(reply)
            i += 1
        await client.send_message(message.channel, 'Top 10 spammers:\n'
                                                   '1: %s\n2: %s\n3: %s\n4: %s\n5: %s\n6: %s\n'
                                                   '7: %s\n8: %s\n9: %s\n10: %s' %
                                  (l1[0],l1[1],l1[2],l1[3],l1[4],l1[5],l1[6],
                                                                           l1[7],l1[8],l1[9]))
        return
    else:
        await client.send_message(message.channel, 'You need to specify a toplist. Available toplists: spammers')
        return

async def cmd_randomquote(client, themessage, input):
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
        content, timestamp, username, mentions = random_message
        sanitized = sanitize_message(content, mentions)
        await client.send_message(themessage.channel, "%s, -- %s, %s" % (sanitized, timestamp, username))

async def cmd_randomcurse(client, themessage, _):
    channel = themessage.channel
    random_message = random_curse()
    if random_message is None:
        await client.send_message(channel, "Sorry, no messages could be found")
    else:
        content, timestamp, username, mentions = random_message
        sanitized = sanitize_message(content, mentions)
        await client.send_message(channel, "%s, -- %s, %s" % (sanitized, timestamp, username))

def register(client):
    return {
        'randomquote': cmd_randomquote,
        'randomcurse': cmd_randomcurse,
        'top': cmd_top
    }
