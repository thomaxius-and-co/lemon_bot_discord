import database as db

def sanitize_message(content, mentions):
    for m in mentions:
        content = content.replace("<@%s>" % m["id"], "@%s" % m["username"])
    return content

def random_quote_from_channel(channel_id):
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT
                m->>'content',
                (m->>'timestamp')::timestamptz AT TIME ZONE 'Europe/Helsinki',
                m->'author'->>'username',
                m->'mentions'
            FROM message
            WHERE m->>'channel_id' = %s
            ORDER BY random()
            LIMIT 1
        """, [channel_id])
        return c.fetchone()

def random_curse():
    with db.connect(readonly = True) as c:
        c.execute("""
            SELECT
                m->>'content',
                (m->>'timestamp')::timestamptz AT TIME ZONE 'Europe/Helsinki',
                m->'author'->>'username',
                m->'mentions'
        from message
        where lower(m->>'content') like '%paska%'  or lower(m->>'content') like '%vitu%' or
        lower(m->>'content') like '%kusipää%' or lower(m->>'content') like '%rotta%' or
        lower(m->>'content') like '%saatana%' or lower(m->>'content') like '%helvet%' or lower(m->>'content') like '%kyrpä%'
        or lower(m->>'content') like '%haista%' or lower(m->>'content') like '%sossupummi%'
        and length(m->>'content') > 6 and m->'author'->>'bot' is null
        order by random()
        limit 1
        """)
        return c.fetchone()

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
        'randomcurse': cmd_randomcurse
    }
