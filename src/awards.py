import database as db
from sqlcommands import get_user_days_in_chat
import asyncio

TROPHY_NAMES = ['Top spammer', 'Least toxic', 'Whosaidit total #1', 'Whosaidit all time high score',
                'Biggest gambling problem']

async def cmd_trophycabinet(client, message, arg):
    oldmessage = await client.send_message(message.channel, 'Please wait while I check the book of winners..')
    user_id = message.author.id
    trophycabinet = await find_user_trophies(user_id)
    msg = ''
    if trophycabinet:
        for trophy in trophycabinet:
            msg += ':trophy:' + trophy + '\n'
        await client.edit_message(oldmessage, 'Your trophies:\n ' + msg + '\n')
    else:
        await client.edit_message(oldmessage, 'You have no trophies.')

async def find_user_trophies(user_id):
    trophycabinet = []
    for trophyname in TROPHY_NAMES:
        playertrophy = await awards.get(trophyname)()
        if user_id == playertrophy:
            trophycabinet.append(trophyname)
    return trophycabinet

async def get_top_spammer():
    user_days_in_chat = await get_user_days_in_chat()
    items = await db.fetch("""
        select
            user_id,
            count(*) as message_count
        from 
            message
        where 
            NOT bot AND content NOT LIKE '!%%'
        group by 
            user_id 
        order by 
            message_count 
        desc 
        limit 10
    """)
    if not items:
        return None
    list_with_msg_per_day = []
    for item in items:
        user_id, message_count = item
        msg_per_day = message_count / user_days_in_chat[user_id]
        new_item = (user_id, round(msg_per_day, 3), message_count)
        list_with_msg_per_day.append(new_item)
    winner = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:1]
    return winner[0][0]

async def get_top_whosaidit():
    items = await db.fetch("""
            with score as 
                (
                select
                    user_id,
                    sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
                    sum(case playeranswer when 'wrong' then 1 else 0 end) as losses
                from 
                    whosaidit_stats_history
                group by 
                    user_id
                )
            select
                user_id
            from 
                score
            join 
                discord_user using (user_id)
            where 
                (wins + losses) >= 20
            order by 
                wins::float / (wins + losses) * 100 
            desc 
            limit 1
    """)
    if not items:
        return None
    for item in items:
        return item['user_id']

async def get_top_whosaidit_score():
    items = await db.fetch("""
        with week_score as 
        (
          select
            date_trunc('week', time) as dateadded,
            user_id,
            sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
            sum(case playeranswer when 'wrong' then 1 else 0 end) as losses,
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) as accuracy,
            least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as bonus,
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count(*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as score,
            max(100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20)) over (partition by date_trunc('week', time)) as weeks_best_score,
            count(user_id) over (partition by date_trunc('week', time)) as players
          from 
            whosaidit_stats_history
          group by 
            user_id, 
            date_trunc('week', time)
          having 
            count(*) >= 20
        )
        select 
            user_id, 
            score
        from 
            week_score
        join 
            discord_user using (user_id)
        where 
            not date_trunc('week', dateadded) = date_trunc('week', current_timestamp) and score = weeks_best_score and players >= 3
        order by score 
        desc 
        limit 1
    """)
    if not items:
        return None
    for item in items:
        return item['user_id']

async def get_top_gambling_addict():
    items = await db.fetch("""
            select
                count(*) as total,
                user_id
            from message
            where 
                content like '!slots%' or content like '!blackjack%'
            group by 
                user_id
            having 
                count(*) >= 100
            order by 
                total desc
            limit 1
    """)
    if not items:
        return None
    for item in items:
        return item['user_id']

async def get_least_toxic():
    items = await db.fetch("""
        with custommessage as (
            select
                coalesce(name, m->'author'->>'username') as name,
                user_id,
                count(*) as message_count
            from 
                message
            join 
                discord_user using (user_id)
            where 
                NOT bot 
            group by coalesce(name, m->'author'->>'username'), user_id
            )
        select
            user_id
        from 
            message
        join 
            custommessage using (user_id)
        where 
            NOT bot and length(content) > 15 and message_count > 300 and name not like 'toxin'
        group by 
            user_id, message_count, name 
        order by (count(*) / message_count::float) * 100 
        desc 
        limit 1
    """)
    if not items:
        return None
    for item in items:
        return item['user_id']

awards = {
    'Top spammer': get_top_spammer,
    'Least toxic': get_least_toxic,
    'Whosaidit total #1': get_top_whosaidit,
    'Whosaidit all time high score': get_top_whosaidit_score,
    'Biggest gambling problem': get_top_gambling_addict
}

def register(client):
    return {
        'trophycabinet': cmd_trophycabinet
    }