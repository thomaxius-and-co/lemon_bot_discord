import database as db
from sqlcommands import get_user_days_in_chat
import asyncio

TROPHY_NAMES = ['Top spammer', 'Least toxic']

async def cmd_trophycabinet(client, message, arg):
    user_id = message.author.id
    trophycabinet = await find_user_trophies(user_id)
    msg = ''
    if trophycabinet:
        for trophy in trophycabinet:
            msg += ':trophy:' + trophy + '\n'
        await client.send_message(message.channel, 'Your trophies:\n' + msg + '\n')
    else:
        await client.send_message(message.channel, 'You have no trophies.')

@asyncio.coroutine
def find_user_trophies(user_id):
    trophycabinet = []
    for trophyname in TROPHY_NAMES:
        playertrophy = yield from awards.get(trophyname)
        if user_id == playertrophy:
            trophycabinet.append(trophyname)
    return trophycabinet

async def get_top_spammer():
    user_days_in_chat = await get_user_days_in_chat()
    items = await db.fetch("""
        select
        user_id,
        count(*) as message_count
         from message
        where NOT bot AND content NOT LIKE '!%%'
        group by user_id order by message_count desc limit 10
    """)
    if not items:
        return None
    list_with_msg_per_day = []
    for item in items:
        user_id, message_count = item
        msg_per_day = message_count / user_days_in_chat[user_id]
        new_item = (user_id, round(msg_per_day,3), message_count)
        list_with_msg_per_day.append(new_item)
    winner = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:1]
    return winner[0][0]

async def get_least_toxic():
    items = await db.fetch("""
        with custommessage as (
            select
            coalesce(name, m->'author'->>'username') as name,
            user_id,
            count(*) as message_count
            from message
            join discord_user using (user_id)
            where NOT bot 
            group by coalesce(name, m->'author'->>'username'), user_id)
        select
        user_id
         from message
        join custommessage using (user_id)
        where NOT bot AND content NOT LIKE '!%%' and length(content) > 15 and message_count > 300 and name not like 'toxin'
        group by user_id, message_count, name order by (count(*) / message_count::float) * 100 desc limit 1
    """)
    if not items:
        return None
    for item in items:
        user_id = item
    return user_id

awards = {
    'Top spammer': get_top_spammer(),
    'Least toxic': get_least_toxic()
}

def register(client):
    return {
    'trophycabinet': cmd_trophycabinet
}