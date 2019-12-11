import database as db
from asyncio import sleep
import logger

log = logger.get("AWARDS")

TROPHY_NAMES = ['Top spammer', 'Whosaidit total #1', 'Whosaidit all time high score',
                'Biggest gambling problem', 'Best grammar', 'Worst grammar', 'Spammer of the week']
CUSTOM_TROPHY_NAMES = []

async def main():
    await get_custom_trophy_names()


async def get_custom_trophy_names():
    trophies = await db.fetch("""
        select
            trophy_name
        from 
            custom_trophies
    """)
    for trophy in trophies:
        CUSTOM_TROPHY_NAMES.append(trophy['trophy_name'])


async def get_custom_trophy_conditions(trophyname):
    trophy = await db.fetch("""
        select
            trophy_conditions
        from 
            custom_trophies
        where
            trophy_name like $1
    """, trophyname)
    for trophy in trophy:
        return trophy['trophy_conditions']


async def delete_trophy(trophyname):
    CUSTOM_TROPHY_NAMES.remove(trophyname)
    await db.execute("""
        delete
        from 
            custom_trophies
        where
            trophy_name like $1
    """, trophyname)
    return


def make_word_filters(words):
    conditions = "content ~* $1"
    params = ["|".join(words)]
    return conditions, params


async def custom_trophy_getter(trophyname):
    custom_trophy_conditions = await get_custom_trophy_conditions(trophyname)
    filters, params = make_word_filters(custom_trophy_conditions.split(', '))
    custom_filter = "AND ({0})".format(filters)
    custom_trophy_id, custom_trophy_winner_name, custom_trophy_winner_determiner = await get_custom_trophy_winner(custom_filter, params)
    return custom_trophy_id, custom_trophy_winner_name, custom_trophy_winner_determiner


async def get_custom_trophy_winner(filters, params):
    user_days_in_chat = await get_user_days_in_chat()
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
            WHERE 
                NOT bot 
                AND content NOT LIKE '!%%'
                AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id) 
                {filters}

            group by 
                coalesce(name, m->'author'->>'username'), user_id)
        select
            user_id,
            name,
            message_count
        from 
            message
        join 
            custommessage using (user_id)
        where 
            NOT bot 
            AND content NOT LIKE '!%%'
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id) 
            {filters}
        group by 
            user_id, message_count, name""".format(filters=filters), *params)
    if not items:
        return None, None, None
    list_with_msg_per_day = []
    for item in items:
        user_id, name, message_count = item
        msg_per_day = message_count / user_days_in_chat[user_id]
        new_item = (user_id, msg_per_day, message_count, name)
        list_with_msg_per_day.append(new_item)
    winner = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:1]
    return winner[0][0], winner[0][3], str(round(winner[0][1],3)) + ' messages per day.'


async def random(filter):
    word_filters, params = make_word_filters(filter)
    return await get_custom_trophy_winner("AND ({0})".format(word_filters), params)


async def get_user_days_in_chat():
    rows = await db.fetch("""
        SELECT
            user_id,
            extract(epoch from current_timestamp - min(ts)) / 60 / 60 / 24
        FROM message
        GROUP BY user_id
    """)
    result = {}
    for row in rows:
        result[row[0]] = row[1]
    # {'244610064038625280': 100.575020288113, '97767102722609152': 384.679490554317 }
    return result


async def cmd_trophycabinet(client, message, arg):
    bot_message = await message.channel.send('Please wait while I check the book of winners..')
    user_id = message.author.id
    trophycabinet = await find_user_trophies(user_id)
    msg = ''
    if trophycabinet:
        for trophy in trophycabinet:
            msg += ':trophy: ' + trophy + '\n'
        await bot_message.edit(content='Your trophies:\n' + msg + '\n')
    else:
        await bot_message.edit(content='You have no trophies.')


async def cmd_deletetrophy(client, message, arg):
    msg = ''
    y = 1
    for x in CUSTOM_TROPHY_NAMES:
        msg += str(y) + '. ' + x + '\n'
        y += 1
    if not arg.isdigit():
        await message.channel.send("You need to specify a trophy ID. Available trophy ID's:\n" + msg)
        return
    if not CUSTOM_TROPHY_NAMES:
        await message.channel.send("There are no throphies")
        return
    if len(CUSTOM_TROPHY_NAMES) <= int(arg) - 1 or (
        int(arg) == 0):  # Even though giving 0 as ID works, It's not we want heh
        await message.channel.send("Invalid trophy ID. Available trophy ID's:\n" + msg)
        return

    trophytobedeleted = CUSTOM_TROPHY_NAMES[int(arg) - 1]
    await delete_trophy(CUSTOM_TROPHY_NAMES[int(arg) - 1])
    await message.channel.send('Succesfully deleted trophy: ' + trophytobedeleted)  # the ugly code above should be just temponary..


async def cmd_listtrophies(client, message, arg):
    if not CUSTOM_TROPHY_NAMES:
        await message.channel.send("There are no throphies.")
        return
    msg = ''
    y = 1
    for x in CUSTOM_TROPHY_NAMES:
        msg += str(y) + '. ' + x + '\n'
        y += 1
    await message.channel.send(msg)


async def cmd_addtrophy(client, message, arg):
    arg = arg.lower()
    error = "Correct usage: name= followed by conditions=, for example:\n``` " \
            "!addtrophy name=Most polite people conditions=Thank you, please, you're welcome```"
    if not (arg[0:5].startswith("name=")) or ("conditions=" not in arg):
        await message.channel.send(error)
        return
    name, conditions = parse_award_info(arg)
    conditions = check_and_remove_invalid_words(conditions)
    if not name or not conditions:
        await message.channel.send(error)
        return
    if not check_and_remove_invalid_words(conditions):
        await message.channel.send("Your trophy contains invalid conditions.")
        return
    if len(name) > 100:
        await message.channel.send("Trophy name can't be over 100 characters.")
        return
    alreadyexists = name in CUSTOM_TROPHY_NAMES
    if alreadyexists:
        await message.channel.send("There is a trophy with a similar name already.")
        return
    await sleep(1)
    await add_custom_award_to_database(name, conditions, message.id)
    CUSTOM_TROPHY_NAMES.append(name)
    await message.channel.send("Succesfully added a trophy.")


def check_and_remove_invalid_words(input):
    # Remove empty words from search, which occured when user typed a comma without text (!top custom test,)
    possible_invalid_list = list(map(lambda x: x.strip(), input.split(',')))

    def checkifsmall(value):
        return len(value) > 0

    valid_list = [word for word in possible_invalid_list if checkifsmall(word)]
    if len(valid_list) == 0:
        return None
    return ', '.join(valid_list)


def parse_award_info(unparsed_arg):
    list_with_args = unparsed_arg.split('conditions=')
    name = str(list_with_args[0]).replace('name=', '', 1)
    conditions = list_with_args[-1]
    return name.rstrip(' '), conditions


async def add_custom_award_to_database(name, conditions, message_id):
    await db.execute("""
        INSERT INTO custom_trophies AS a
        (message_id, trophy_name, trophy_conditions)
        VALUES ($1, $2, $3)""", message_id, name, conditions)
    log.info('Added custom award to the database: message_id %s, trophy name: %s, conditions: %s', message_id, name, conditions)


async def cmd_alltrophies(client, message, arg):
    bot_message = await message.channel.send('Please wait while I check the book of winners..')
    trophycabinet = await find_all_trophies()
    msg = ''
    if trophycabinet:
        for trophy in trophycabinet:
            msg += ':trophy: ' + trophy + '\n'
        log.info(msg + '\n')
        await bot_message.edit(content=msg + '\n')
    else:
        await bot_message.edit(content='Nobody has won a trophy yet.')


async def find_user_trophies(user_id):
    trophycabinet = []
    for trophyname in TROPHY_NAMES:
        trophy_winner_id, trophy_winner_name, trophy_winner_determiner = await trophies.get(trophyname)()
        if user_id == trophy_winner_id:
            trophycabinet.append(trophyname)
    for trophyname in CUSTOM_TROPHY_NAMES:
        trophy_winner_id, trophy_winner_name, trophy_winner_determiner = await custom_trophy_getter(trophyname)
        if user_id == trophy_winner_id:
            trophycabinet.append(trophyname)
    return trophycabinet


async def find_all_trophies():
    trophycabinet = []
    for trophyname in TROPHY_NAMES:
        trophy_winner_id, trophy_winner_name, trophy_winner_determiner = await trophies.get(trophyname)()
        if trophy_winner_name:
            trophycabinet.append(trophyname + '  -  ' + trophy_winner_name + ' with ' + trophy_winner_determiner)
    for trophyname in CUSTOM_TROPHY_NAMES:
        trophy_winner_id, trophy_winner_name, trophy_winner_determiner = await custom_trophy_getter(trophyname)
        if trophy_winner_name:
            trophycabinet.append(trophyname + '  -  ' + trophy_winner_name + ' with ' + trophy_winner_determiner)
    return trophycabinet


async def get_top_spammer():
    user_days_in_chat = await get_user_days_in_chat()
    items = await db.fetch("""
        select
            user_id,
            name as username,
            count(*) as message_count
        from 
            message
        join
             discord_user using (user_id)
        where 
            NOT bot 
            AND content NOT LIKE '!%%'
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
        group by 
            user_id, username
        order by 
            message_count 
        desc 
        limit 10
    """)
    if not items:
        return None, None, None
    list_with_msg_per_day = []
    for item in items:
        user_id, name, message_count = item
        msg_per_day = message_count / user_days_in_chat[user_id]
        new_item = (user_id, round(msg_per_day, 1), message_count, name)
        list_with_msg_per_day.append(new_item)
    winner = sorted(list_with_msg_per_day, key=lambda x: x[1], reverse=True)[:1]
    return winner[0][0], winner[0][3], str(winner[0][1]) + ' messages per day.'


async def get_spammer_of_the_week():
    items = await db.fetch("""
        select
            user_id,
            name as username,
            count(*) as message_count
        from 
            message
        join
             discord_user using (user_id)
        where 
            NOT bot 
            AND content NOT LIKE '!%%'
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            AND date_part('week',ts) = date_part('week', current_timestamp) - 1
        group by 
            user_id, username
        order by 
            message_count 
        desc 
        limit 1
    """)
    if not items:
        return None, None, None
    for item in items:
        user_id, name, message_count = item
        return user_id, name, str(message_count) + ' messages.'


async def get_top_whosaidit():
    items = await db.fetch("""
        with score as 
            (
            select
                user_id,
                name as username,
                sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
                sum(case playeranswer when 'wrong' then 1 else 0 end) as losses
            from 
                whosaidit_stats_history
            join
                discord_user using (user_id)
            group by 
                user_id,
                username
            )
        select
            user_id,
            username,
            wins::float / (wins + losses) * 100 as score
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
        return None, None, None
    for item in items:
        user_id, name, score = item
        return user_id, name, str(round(score,3)) + ' pct.'


async def get_top_whosaidit_score():
    items = await db.fetch("""
        with week_score as 
        (
          select
            date_trunc('week', time) as dateadded,
            user_id,
            name as username,
            sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
            sum(case playeranswer when 'wrong' then 1 else 0 end) as losses,
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) as accuracy,
            least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as bonus,
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count(*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as score,
            max(100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20)) over (partition by date_trunc('week', time)) as weeks_best_score,
            count(user_id) over (partition by date_trunc('week', time)) as players
          from 
            whosaidit_stats_history
            join 
            discord_user using (user_id)
          group by 
            user_id, 
            date_trunc('week', time),
            username
          having 
            count(*) >= 20
        )
        select 
            user_id,
            username,
            score
        from 
            week_score
        join 
            discord_user using (user_id)
        where 
            not date_trunc('week', dateadded) = date_trunc('week', current_timestamp) and score = weeks_best_score and players >= 2
        order by score 
        desc 
        limit 1
    """)
    if not items:
        return None, None, None
    for item in items:
        user_id, name, score = item
        return user_id, name, str(round(score, 1)) + ' pct'


async def get_top_gambling_addict():
    items = await db.fetch("""
            select
                user_id,
                name,
                count(*) as total
            from 
                message
            JOIN 
                discord_user USING (user_id)
            where 
                content like '!slots%' or content like '!blackjack%'
            group by 
                user_id, name
            having 
                count(*) >= 100
            order by 
                count(*) desc
            limit 1
    """)  # this should be replaced with a query that searches from the respected casino games' tables
    if not items:
        return None, None, None
    for item in items:
        user_id, name, total = item
        return user_id, name, str(total) + ' games.'


async def get_best_grammar():
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
                AND content not LIKE '!%%'
                AND content not like '%http%'
                AND content not like '%www%'
                AND content ~* '^[A-ZÅÄÖ]'
                AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            group by 
                coalesce(name, m->'author'->>'username'), user_id)
        select
            user_id,
            name,
            (count(*) / message_count::float) * 100 as pctoftotal
         from 
            message
        join 
            custommessage using (user_id)
        where 
            NOT bot
            and message_count > 300
            AND content NOT LIKE '!%%'
            AND content ~ '^[A-ZÅÄÖ][a-zöäå]'            
            AND content NOT LIKE '%www%'
            AND content NOT LIKE '%http%'
            or content ~* '[A-ZÅÄÖ]\?$'
            or content ~* '[A-ZÅÄÖ]\.$'
            or content ~* '[A-ZÅÄÖ]!$'
            or (length(content) > 25 
            and content like '%,%')
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
        group by 
            user_id, message_count, name
        HAVING
            count(*) > 300
        order by 
            pctoftotal desc
    """)
    if not items:
        return None, None, None
    for item in items:
        user_id, name, pctoftotal = item
        return user_id, name, str(round(pctoftotal, 1)) + ' % good messages.'


async def get_worst_grammar():
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
                AND content not LIKE '!%%'
                AND content not like '%http%'
               AND content not like '%www%'
                AND content ~* '^[A-ZÅÄÖ]'
                and name not like 'toxin'
            group by 
                coalesce(name, m->'author'->>'username'), user_id)
        select
                user_id,
                name,
                100 - ((count(*) / message_count::float) * 100) as pct
        from 
            message
        join 
            custommessage using (user_id)
        where 
            NOT bot
            and message_count > 300
            and name not like 'toxin'
            AND content NOT LIKE '!%%'
            AND content ~ '^[A-ZÅÄÖ][a-zöäå]'            
            AND content NOT LIKE '%www%'
            AND content NOT LIKE '%http%'
            or content ~* '[A-ZÅÄÖ]\?$'
            or content ~* '[A-ZÅÄÖ]\.$'
            or content ~* '[A-ZÅÄÖ]!$'
            or (length(content) > 25 and content like '%,%')
        group by 
            user_id, message_count, name 
        HAVING
            count(*) > 300
        order by 
            (count(*) / message_count::float) * 100 asc
        limit
            1
    """)
    if not items:
        return None, None, None
    for item in items:
        user_id, name, pct = item
        return user_id, name, str(round(pct, 1)) + ' % bad messages.'


trophies = {
    'Top spammer': get_top_spammer,
    'Whosaidit total #1': get_top_whosaidit,
    'Whosaidit all time high score': get_top_whosaidit_score,
    'Biggest gambling problem': get_top_gambling_addict,
    'Best grammar': get_best_grammar,
    'Worst grammar': get_worst_grammar,
    'Spammer of the week': get_spammer_of_the_week
}

def register(client):
    return {
        'trophycabinet': cmd_trophycabinet,
        'alltrophies': cmd_alltrophies,
        'addtrophy': cmd_addtrophy,
        'deletetrophy': cmd_deletetrophy,
        'listtrophies': cmd_listtrophies
    }