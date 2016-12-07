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

def register(client):
    return {
        'randomquote': cmd_randomquote,
    }
