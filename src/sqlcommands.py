import asyncio
import discord
import re
import json
import database as db
from tablemaker import tablemaker
import emoji
import random as rand
from datetime import datetime, timedelta
from lan import delta_to_tuple
from time_util import as_utc, to_helsinki
from trophies import CUSTOM_TROPHY_NAMES, get_custom_trophy_conditions
from util import split_message_for_sending
import logger

log = logger.get("SQLCOMMANDS")
playing_dict = {}


def sanitize_message(content, mentions):
    for m in mentions:
        content = content.replace("<@%s>" % m["id"], "@%s" % m["username"])
    return content



async def send_quote(client, channel, random_message) -> discord.Message:
    content, timestamp, mentions, user_id, name, avatar = random_message
    formatted_timestamp = timestamp.strftime("%a %d-%m-%Y %H:%M:%S")
    mentions = json.loads(mentions)
    sanitized = sanitize_message(content, mentions)
    avatar_url = "https://cdn.discordapp.com/avatars/{user_id}/{avatar}.jpg".format(user_id=user_id, avatar=avatar)

    embed = discord.Embed(description=sanitized)
    embed.set_author(name=name, icon_url=avatar_url)
    embed.set_footer(text=formatted_timestamp)
    return await channel.send(embed=embed)


async def random_message_with_filter(filters, params):
    return await db.fetchrow("""
        SELECT
            content,
            ts::timestamptz AT TIME ZONE 'Europe/Helsinki',
            m->'mentions',
            user_id,
            name,
            m->'author'->>'avatar' as avatar
        FROM 
            message 
        JOIN 
            discord_user USING (user_id)
        WHERE 
            length(content) > 6 
            AND content NOT LIKE '!%%' 
            AND NOT bot 
            {filters} 
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
        ORDER BY 
            random() LIMIT 1
    """.format(filters=filters), *params)


async def legendary_quote(guild_id: str):
    return await db.fetchrow(f"""
        SELECT
            content,
            ts::timestamptz AT TIME ZONE 'Europe/Helsinki',
            m->'mentions',
            user_id,
            name,
            m->'author'->>'avatar' as avatar
        FROM 
            message m
        JOIN 
            discord_user USING (user_id)
        JOIN
            legendary_quotes l USING (message_id)
        WHERE 
            length(content) > 6
            AND guild_id = $1
        ORDER BY 
            random() LIMIT 1
    """, guild_id)


async def get_blackjack_toplist():
    items = await db.fetch("""
        SELECT
            (wins_bj / (wins_bj + losses_bj)) * 100,
            wins_bj,
            wins_bj + losses_bj,
            name,
            losses_bj,
            surrenders,
            ties,
            moneyspent_bj,
            moneywon_bj,
            concat('#', row_number() OVER (ORDER BY  (wins_bj / (wins_bj + losses_bj)) * 100 desc)) AS rank
        FROM 
            casino_stats
        JOIN 
            discord_user USING (user_id)
        WHERE
            (wins_bj + losses_bj) > 1
        ORDER BY 
            (wins_bj / (wins_bj + losses_bj)) * 100 DESC
        LIMIT 10
    """)
    if len(items) == 0:
        return None, None
    toplist = []
    for item in items:
        pct, wins, total, name, losses, surrenders, ties, moneyspent, moneywon, rank = item
        new_item = (name[0:10], rank, total, wins, losses, surrenders, ties, moneyspent, round(moneywon), round(pct, 3))
        toplist.append(new_item)
    # toplist = addsymboltolist(toplist,9,' %')
    return tablemaker(['NAME', 'RANK', 'TOT', 'W', 'L', 'S', 'T', '$ SPENT', '$ WON', '%'], toplist), len(toplist)


async def get_slots_toplist():
    items = await db.fetch("""
        SELECT
            name,
            concat('#', row_number() OVER (ORDER BY  (wins_slots / (wins_slots + losses_slots)) * 100 desc)) AS rank,
            wins_slots + losses_slots,
            wins_slots,
            losses_slots,
            moneyspent_slots,
            moneywon_slots,
            moneywon_slots - moneyspent_slots as profit,
            (wins_slots / (wins_slots + losses_slots)) * 100
        FROM 
            casino_stats
        JOIN 
            discord_user USING (user_id)
        WHERE 
            AND (wins_slots + losses_slots) > 100
            
        ORDER BY 
            moneywon_slots - moneyspent_slots DESC
        LIMIT 10
    """)
    if len(items) == 0:
        return None, None
    toplist = []
    for item in items:
        name, rank, total, wins, losses, moneyspent, moneywon, profit, pct = item
        new_item = (name[0:10], rank, total, wins, losses, moneyspent, moneywon, profit, round(pct, 3))
        toplist.append(new_item)
    # toplist = addsymboltolist(toplist,7,' %')
    return tablemaker(['NAME', 'RANK', 'TOT', 'W', 'L', '$ SPENT', '$ WON', '$ PROFIT', '%'], toplist), len(toplist)


async def get_quote_for_quote_game(guild_id, name):
    for properquote in range(0, 10):
        quote = await db.fetchrow("""
        SELECT
            content,
            coalesce(name, m->'author'->>'username'),
            m->'mentions',
            message_id
        FROM 
            message 
        JOIN 
            discord_user USING (user_id)
        WHERE 
            guild_id = $1
            AND length(content) > 12
            AND length(content) < 1000 
            AND content NOT LIKE '!%%' 
            AND content NOT LIKE '%wwww%'
            AND content NOT LIKE '%http%' 
            AND content NOT LIKE '%.com%' 
            AND content NOT LIKE '%.fi%'
            AND content ~* '^[A-ZÅÄÖ]'
            AND NOT bot 
            AND coalesce(name, m->'author'->>'username') LIKE $2
        ORDER BY 
            random()
        LIMIT 
            1
    """, guild_id, name)
        if not invalid_quote(quote['content']):
            log.info('This quote is good {0}'.format(quote['content'].encode("utf-8")))
            return quote
        else:
            log.info('This quote is bad, fetching a new one.. {0}'.format(quote['content'].encode("utf-8")))
    return None


def invalid_quote(quote):
    def is_custom_emoji(quote):  # checks if quote is an emoji (ends and begins in :)
        return quote.startswith('<:') and quote.endswith('>')

    def is_emoji(quote):  # checks if quote is an emoji (ends and begins in :)
        return quote.startswith(":") and quote.endswith(":")

    def is_gibberish(quote):  # checks if quote consists of 6 different letters
        return len(set(quote)) < 6

    return is_gibberish(quote) or is_emoji(str(quote)) or is_custom_emoji(str(quote))


def make_word_filters(guild_id, words):
    conditions = "content ~* $1 AND guild_id = $2"
    params = ["|".join(words), str(guild_id)]
    return conditions, params


async def random(guild_id, filter):
    word_filters, params = make_word_filters(guild_id, filter)
    return await random_message_with_filter("AND ({0})".format(word_filters), params)


async def random_quote_from_channel(channel_id):
    return await random_message_with_filter("AND m->>'channel_id' = $1", [str(channel_id)])


async def get_user_days_in_chat(guild_id: str):
    rows = await db.fetch("""
        SELECT
            user_id,
            extract(epoch from current_timestamp - min(ts)) / 60 / 60 / 24
        FROM 
            message
        WHERE
            guild_id = $1
        GROUP BY user_id
    """, guild_id)
    result = {}
    for row in rows:
        result[row[0]] = row[1]
    # {'244610064038625280': 100.575020288113, '97767102722609152': 384.679490554317 }
    return result


async def get_best_grammar(guild_id: str):
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
                guild_id = $1
                AND NOT bot 
                AND content not LIKE '!%%'
                AND content not like '%http%'
                AND content not like '%www%'
                AND content ~* '^[A-ZÅÄÖ]'
                AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            group by 
                coalesce(name, m->'author'->>'username'), user_id)
        select
            name,
            user_id,
                message_count,
                count(*) as count,
                (count(*) / message_count::float) * 100 as pctoftotal
         from 
            message
        join 
            custommessage using (user_id)
        where
            guild_id = $1
            AND NOT bot
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
    """, guild_id)
    if not items:
        return None, None
    toplist = []
    for item in items:
        name, user_id, message_count, good_messages, bs_percentage = item
        new_item = (name[0:10], message_count, good_messages, round(bs_percentage, 3))
        toplist.append(new_item)
    top_ten = add_rank_to_list(sorted(toplist, key=lambda x: x[3], reverse=True)[:10])
    return tablemaker(['NAME', 'RANK', 'TOTAL MSGS', 'GOOD MSGS', 'GOOD GRAMMAR %', emoji.FIRST_PLACE_MEDAL +
                       emoji.SECOND_PLACE_MEDAL + emoji.THIRD_PLACE_MEDAL], top_ten), len(top_ten)


async def get_worst_grammar(guild_id: str):
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
                guild_id = $1 
                AND NOT bot 
                AND content not LIKE '!%%'
                AND content not like '%http%'
               AND content not like '%www%'
                AND content ~* '^[A-ZÅÄÖ]'
                AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            group by 
                coalesce(name, m->'author'->>'username'), user_id)
        select
            name,
            user_id,
                message_count,
                message_count - count(*) as bad_messages,
                100 - (count(*) / message_count::float) * 100 as pctoftotal
         from 
            message
        join 
            custommessage using (user_id)
        where
            guild_id = $1
            AND NOT bot
            and message_count > 300
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            AND content NOT LIKE '!%%'
            AND content ~ '^[A-ZÅÄÖ][a-zöäå]'            
            AND content NOT LIKE '%www%'
            AND content NOT LIKE '%http%'
            or content ~* '[A-ZÅÄÖ]\?$'
            or content ~* '[A-ZÅÄÖ]\.$'
            or content ~* '[A-ZÅÄÖ]!$'
            or (length(content) > 25 
            and content like '%,%')
        group by 
            user_id, message_count, name
        HAVING
            count(*) > 300
        order by 
            pctoftotal desc
    """, guild_id)
    if not items:
        return None, None
    toplist = []
    for item in items:
        name, user_id, message_count, bad_messages, bs_percentage = item
        new_item = (name[0:10], message_count, bad_messages, round(bs_percentage, 3))
        toplist.append(new_item)
    top_ten = add_rank_to_list(sorted(toplist, key=lambda x: x[3], reverse=True)[:10])
    return tablemaker(
        ['NAME', 'RANK', 'TOTAL MSGS', 'BAD MSGS', 'BAD GRAMMAR %', emoji.FIRST_PLACE_MEDAL +
         emoji.SECOND_PLACE_MEDAL + emoji.THIRD_PLACE_MEDAL], top_ten), len(top_ten)


async def top_message_counts(filters, params, excludecommands, guild_id: str):
    # todo: fix dangerous query
    sql_excludecommands = "AND content NOT LIKE '!%%'" if excludecommands else ""
    user_days_in_chat = await get_user_days_in_chat(guild_id)
    items = await db.fetch("""
        with custommessage as (
            SELECT
                coalesce(name, m->'author'->>'username') as name,
                user_id,
                count(*) as message_count
            FROM 
                message
            JOIN 
                discord_user using (user_id)
            WHERE 
                guild_id = '{guild_id}'
                AND NOT bot 
                AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id) 
                {sql_excludecommands} 
                {filters}
            GROUP BY 
                coalesce(name, m->'author'->>'username'), user_id)
        SELECT
            name,
            user_id,
            message_count,
            (message_count /  sum(count(*)) over()) * 100 as pctoftotal
        FROM 
            message
        JOIN  
            custommessage using (user_id)
        WHERE 
            guild_id = '{guild_id}'
            AND NOT bot
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
            {sql_excludecommands} 
            {filters}
        GROUP BY 
            user_id, message_count, name 
        ORDER BY 
            pctoftotal DESC
    """.format(guild_id=guild_id, filters=filters, sql_excludecommands=sql_excludecommands), *params)
    if not items:
        return None, None
    list_with_msg_per_day = []
    for item in items:
        name, user_id, message_count, pct_of_total = item
        msg_per_day = message_count / user_days_in_chat[user_id]
        new_item = (name, message_count, round(msg_per_day, 3), round(pct_of_total, 3))
        list_with_msg_per_day.append(new_item)
    top_ten = add_rank_to_list(sorted(list_with_msg_per_day, key=lambda x: x[2], reverse=True)[:10])
    return tablemaker(['NAME', 'RANK', 'TOTAL', 'MSG PER DAY', '% OF TOTAL', emoji.FIRST_PLACE_MEDAL +
                       emoji.SECOND_PLACE_MEDAL + emoji.THIRD_PLACE_MEDAL], top_ten), len(top_ten)


def add_rank_to_list(list_without_rank_and_medal):  # todo: get rid of this shit
    rank = 1
    new_list = []
    for item in list_without_rank_and_medal:
        if rank == 1:
            medal = '  ' + emoji.FIRST_PLACE_MEDAL
        elif rank == 2:
            medal = '  ' + emoji.SECOND_PLACE_MEDAL
        elif rank == 3:
            medal = '  ' + emoji.THIRD_PLACE_MEDAL
        else:
            medal = ''
        a, b, c, d = item
        new_list.append((a, '#' + str(rank), b, c, d, medal))
        rank += 1
    return new_list


def add_symbol_to_list(lst, position, symbol):
    new_list = []
    for item in lst:
        old_item = list(item)
        single_item = old_item[position]
        new_item = str(single_item) + symbol
        old_item.remove(single_item)
        old_item.append(new_item)
        new_list.append(tuple(old_item))
    return new_list


async def check_if_enough_messages_to_play(guild_id):
    items = await db.fetch("""
        SELECT
            coalesce(name, m->'author'->>'username') AS name
        FROM 
            message 
        JOIN 
            discord_user USING (user_id)
        WHERE 
            guild_id = $1
            AND NOT bot
            AND length(content) > 12 
            AND content NOT LIKE '!%%' 
            AND content NOT LIKE '%wwww%'
            AND content NOT LIKE '%http%' 
            AND content NOT LIKE '%.com%' 
            AND content NOT LIKE '%.fi%'
            AND content ~* '^[A-ZÅÄÖ]'
            AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
        GROUP BY 
            coalesce(name, m->'author'->>'username'), user_id
        HAVING 
            count(*) >= 500""", guild_id)
    return [item['name'] for item in items]


def check_length(x, i):
    return len(str(x[i]))


async def cmd_top(client, message, input):
    guild_id = str(message.guild.id)
    if not input:
        await message.channel.send('You need to specify a toplist. Available toplists: spammers,'
                                   ' custom <words separated by comma>')
        return

    excludecommands = input[0] != '!'

    input = input.lower()
    if input == 'spammers' or input == '!spammers':
        reply, amount_of_people = await top_message_counts("AND 1 = $1", [1], excludecommands, guild_id)
        if not reply or not amount_of_people:
            await message.channel.send('Not enough chat logged into the database to form a toplist.')
            return

        parameter = '(commands included)' if not excludecommands else '(commands not included)'
        header = 'Top %s spammers %s\n' % (amount_of_people, parameter)
        await message.channel.send('```' + header + reply + '```')
        return

    elif input == 'bestgrammar':
        reply, amount_of_people = await get_best_grammar(guild_id)
        if not reply or not amount_of_people:
            await message.channel.send('Not enough chat logged into the database to form a toplist.')
            return

        header = 'Top %s people with the best grammar (most messages written with proper grammar)\n' % (amount_of_people)
        await message.channel.send('```' + header + reply + '```')
        return

    elif input == 'worstgrammar':
        reply, amount_of_people = await get_worst_grammar(guild_id)
        if not reply or not amount_of_people:
            await message.channel.send('Not enough chat logged into the database to form a toplist.')
            return

        header = 'Top %s people with the worst grammar (most messages written with bad grammar)\n' % (amount_of_people)
        await message.channel.send('```' + header + reply + '```')
        return

    elif input[0:6] == 'custom' or input[0:7] == '!custom':
        custom_words = await get_custom_words(input, message, client)
        if not custom_words:
            return
        filters, params = make_word_filters(guild_id, custom_words)
        custom_filter = "AND ({0})".format(filters)
        reply, amount_of_people = await top_message_counts(custom_filter, params, excludecommands, guild_id)
        if not reply or not amount_of_people:
            await message.channel.send('Not enough chat logged into the database to form a toplist.')
            return

        word = 'word' if len(custom_words) == 1 else 'words'
        parameter = '(commands not included)' if excludecommands else '(commands included)'

        title = 'Top %s users of the %s: %s %s' % (amount_of_people, word, ', '.join(custom_words), parameter)

        await message.channel.send(('```%s \n' % title + reply + '```'))
        return

    elif input == 'whosaidit':
        ranking, amount_of_people = await get_whosaidit_ranking()
        if not ranking or not amount_of_people:
            await message.channel.send('Not enough players to form a toplist.')
            return

        title = 'Top %s players of !whosaidit (need 20 games to qualify):' % (amount_of_people)
        time_until_reset = await get_time_until_reset_message()
        await message.channel.send(('```%s \n' % title + ranking + '\n' + time_until_reset + '```'))
        return

    elif input == 'whosaidit weekly':
        weekly_winners_list = await get_whosaidit_weekly_ranking()
        if not weekly_winners_list:
            await message.channel.send('Not enough players to form a weekly toplist.')
            return

        title = 'Weekly whosaidit winners:'
        await message.channel.send((title + '\n' + '```' + weekly_winners_list + '```'))
        return
    elif input == 'blackjack' or input == 'bj':
        reply, amount_of_people = await get_blackjack_toplist()
        if not reply or not amount_of_people:
            await message.channel.send('Not enough players to form a toplist.')
            return

        header = 'Top %s blackjack players\n' % (amount_of_people)
        await message.channel.send('```' + header + reply + '```')
        return

    elif input == 'slots':
        reply, amount_of_people = await get_slots_toplist()
        jackpot = await get_jackpot()
        if not reply or not amount_of_people:
            await message.channel.send('Not enough players to form a toplist. (need 100 games to qualify')
            return

        header = 'Top %s slots players (need 100 games to qualify)\n' % (amount_of_people)
        jackpot = '\nCurrent jackpot: %s$' % (jackpot['jackpot'])
        await message.channel.send('```' + header + reply + jackpot + '```')
        return

    for trophy in CUSTOM_TROPHY_NAMES:
        _trophy = trophy.lower()
        if input == _trophy:
            custom_words = await get_custom_trophy_conditions(trophy)  # todo?
            custom_words = await get_custom_words(custom_words, message, client)
            if not custom_words:
                return
            filters, params = make_word_filters(guild_id, custom_words)
            custom_filter = "AND ({0})".format(filters)
            reply, amount_of_people = await top_message_counts(custom_filter, params, excludecommands, guild_id)
            if not reply or not amount_of_people:
                await message.channel.send('Nobody has this trophy.')
                return

            word = 'word' if len(custom_words) == 1 else 'words'
            parameter = '(commands not included)' if excludecommands else '(commands included)'

            title = 'Leaderboard of trophy %s (top %s users of the %s: %s %s)' % (
            trophy, amount_of_people, word, ', '.join(custom_words), parameter)

            await message.channel.send(('```%s \n' % title + reply + '```'))
            return
    else:
        msg_content = "Unknown list. Available lists: spammers, whosaidit, blackjack, slots, bestgrammar, custom <words separated by comma>"
        if CUSTOM_TROPHY_NAMES:
            msg_content += ", " + ", ".join(CUSTOM_TROPHY_NAMES)
        for msg in split_message_for_sending([msg_content], join_str="\n\n"):
            await message.channel.send(msg)
        return


async def get_jackpot():
    return await db.fetchrow("SELECT jackpot from casino_jackpot")


async def get_whosaidit_ranking():
    items = await db.fetch("""
    with score as (
            select
                user_id,
                sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
                sum(case playeranswer when 'wrong' then 1 else 0 end) as losses
              from 
                    whosaidit_stats_history
              where 
                    date_trunc('week', time) = date_trunc('week', current_timestamp)
              group by user_id)
            select
                    wins::float / (wins + losses) * 100 as ratio,
                    least(0.20 * wins, 20) as bonuspct,
                    wins,
                    wins + losses as total,
                    name,
                    concat('#', row_number() OVER (ORDER BY (wins::float / (wins + losses) * 100)+ least(0.20* wins, 20) desc)) AS rank
            from
                score
            join 
                discord_user using (user_id)
            where 
                (wins + losses) >= 20
            order by 
                rank asc""")
    if len(items) == 0:
        return None, None
    toplist = []
    for item in items:
        pct, bonuspct, correct, total, name, rank = item
        new_item = (name, rank, correct, total, round(pct, 3), bonuspct)
        toplist.append(new_item)
    return tablemaker(['NAME', 'RANK', 'CORRECT', 'TOTAL', 'ACCURACY', 'BONUS PCT'], toplist), len(toplist)


async def get_whosaidit_weekly_ranking():
    items = await db.fetch("""
    -- week_score = score per pelaaja per viikko
        with week_score as (
          select
            date_trunc('week', time) as dateadded,
            user_id,
            sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
            sum(case playeranswer when 'wrong' then 1 else 0 end) as losses,
            -- accuracy
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) as accuracy,
            -- bonus
            least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as bonus,
            -- score = accuracy + bonus
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count(*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as score,
            -- MAGIC! weeks_best_score on kyseisen viikon paras score
            max(100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20)) over (partition by date_trunc('week', time)) as weeks_best_score,
            -- more magic
            count(user_id) over (partition by date_trunc('week', time)) as players
          from whosaidit_stats_history
          group by user_id, date_trunc('week', time)
          having count(*) >= 20
        )

        select dateadded, name, score, wins, losses, accuracy, bonus, players, wins + losses as total
        from week_score
        join discord_user using (user_id)
        -- Valitaan vain rivit, joilla score on viikon paras score, eli voittajat
          where not 
                AND date_trunc('week', dateadded) = date_trunc('week', current_timestamp) and score = weeks_best_score and players >= 2
        order by dateadded desc""")
    if len(items) == 0:
        return None, None
    toplist = []
    for item in items:
        dateadded, name, score, wins, losses, accuracy, bonus, players, total = item
        new_item = (get_week_with_year(dateadded), name, round(score, 3), wins, losses, total)
        toplist.append(new_item)
    return tablemaker(['WEEK', 'NAME', 'SCORE', 'WINS', 'LOSSES', 'TOTAL'], toplist)


def get_week_with_year(datetimeobject):
    return datetimeobject.strftime("%V") + '/' + datetimeobject.strftime(
        "%Y")  # Week number/year todo: fix the issue of last year's days being problematic


async def get_custom_words(input, message, client):
    # Remove empty words from search, which occured when user typed a comma without text (!top custom test,)
    custom_words = list(map(lambda x: x.strip(), re.sub('!?custom', '', input).split(',')))

    def check_if_small(value):
        return len(value) > 0

    custom_words = [word for word in custom_words if check_if_small(word)]
    if len(custom_words) == 0:
        await message.channel.send("You need to specify custom words to search for.")
        return
    return custom_words


async def add_user_to_playing_dict(guild_id, author):
    if guild_id not in playing_dict:
        playing_dict.update({guild_id: [author]})
    else:
        guild_playinglist = playing_dict.get(guild_id)
        if author not in guild_playinglist:
            guild_playinglist.append(author)
            dict.update({guild_id: guild_playinglist})


async def remove_user_from_playing_dict(guild_id, author):
    playing_dict.get(guild_id).remove(author)


async def is_playing(guild_id, name):
    playing_list = playing_dict.get(guild_id, [])
    return name in playing_list


async def cmd_randomquote(client, themessage, input):
    guild_id = themessage.guild.id
    channel = themessage.channel
    if await is_playing(guild_id, themessage.author):
        await channel.send("Sorry, cheating is not allowed. (You are playing whosaidit.)")
        return
    if input is not None and 'custom' in input.lower()[0:6]:
        custom_words = await get_custom_words(input, themessage, client)
        if not custom_words:
            return
        random_message = await random(guild_id, custom_words)
        if random_message is None:
            await channel.send("Sorry, no messages could be found")
            return
        await send_quote(client, channel, random_message)
        return
    channel = None
    if input is None:
        channel = themessage.channel
    else:
        guild = themessage.channel.guild
        for c in guild.channels:
            if c.name == input:
                channel = c
                break

        if channel is None:
            await themessage.channel.send("Sorry, I couldn't find such channel")
            return

    random_message = await random_quote_from_channel(channel.id)
    if random_message is None:
        await themessage.channel.send("Sorry, no messages could be found")
    else:
        await send_quote(client, themessage.channel, random_message)


async def cmd_legendary_quote(client, message, arg):
    quote = await legendary_quote(str(message.guild.id))
    if quote is None:
        await message.channel.send("Sorry, no messages could be found")
    else:
        sent_message = await send_quote(client, message.channel, quote)
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")


async def cmd_whosaidit(client, message, _):
    if not await is_playing(message.guild.id, message.author):
        await add_user_to_playing_dict(message.guild.id, message.author)
    else:
        await message.channel.send('%s: Cannot play: You already have an unfinished game.' % message.author.name)
        return
    await do_whosaidit(client, message, _)


async def do_whosaidit(client, message, _):
    guild_id = str(message.guild.id)
    channel = message.channel
    listofspammers = await check_if_enough_messages_to_play(guild_id)
    if not listofspammers or len(listofspammers) < 5:
        await channel.send('Not enough chat logged to play.')
        await remove_user_from_playing_dict(message.guild.id, message.author)
        return
    rand.shuffle(listofspammers)
    name = rand.choice(listofspammers)
    listofspammers.remove(name)
    quote = await get_quote_for_quote_game(guild_id, name)
    if not quote:
        await channel.send('Not enough chat logged to play.')  # I guess this is a pretty
        #  rare occasion, # but just in case
        await remove_user_from_playing_dict(message.guild.id, message.author)
        return
    await send_question(client, message, listofspammers, quote)


async def send_question(client, message, listofspammers, thequote):
    correct_name = thequote[1]
    message_id = thequote[3]
    sanitized_question = sanitize_message(thequote[0], json.loads(thequote[2]))
    options = [listofspammers[0].lower(), listofspammers[1].lower(), listofspammers[2].lower(),
               listofspammers[3].lower(),
               correct_name.lower()]
    rand.shuffle(options)
    await message.channel.send("It's time to play 'Who said it?' !\n %s, who"
                               " said the following:\n ""*%s*""\n Options: %s. You have 15 seconds to answer!"
                               % (message.author.name, sanitized_question, ', '.join(options)))

    try:
        answer = await get_response(client, correct_name, options, message)
        if answer and answer == 'correct':
            await message.channel.send("%s: Correct! It was %s" % (message.author.name, correct_name))
        elif answer and answer == 'wrong':
            await message.channel.send("%s: Wrong! It was %s" % (message.author.name, correct_name))
    except asyncio.TimeoutError:
        answer = 'wrong'
        await message.channel.send("%s: Time is up! The answer was %s" % (message.author.name, correct_name))
    await save_stats_history(message.author.id, message_id, sanitized_question, correct_name, answer)
    await remove_user_from_playing_dict(message.guild.id, message.author)
    return


async def get_response(client, name, options, message):
    def is_response(m):
        is_reply = m.channel == message.channel and m.author == message.author
        is_option = m.content.lower() == name.lower() or m.content.lower() in options
        return is_reply and is_option

    answer: discord.Message = await client.wait_for("message", timeout=15, check=is_response)
    if answer:
        answer_content = answer.content.lower()
        if answer_content == name.lower():
            return 'correct'
        return 'wrong'


async def save_stats_history(userid, message_id, sanitizedquestion, correctname, answer):
    correct = correctname == answer
    await db.execute("""
        INSERT INTO whosaidit_stats_history AS a
        (user_id, message_id, quote, correctname, playeranswer, correct, time, week)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, userid, message_id, sanitizedquestion, correctname, answer, 1 if correct else 0, datetime.today(),
                     datetime.today().isocalendar()[1])
    log.info("save_stats_history: saved game result for user {0}: {1}".format(userid, correct))


async def cmd_add_excluded_user(client, message, arg):
    if not arg:
        await message.channel.send('Usage: !addexcludeduser <userID>. '
                                   'or highlight someone: !addexcludeduser @Thomaxius')
        return
    user_id: str = arg[:-1].lstrip('<@')
    if not user_id.isdigit():
        await message.channel.send('UserID has to be numeric.')
        return
    excluded_users = await get_excluded_users()
    if user_id in excluded_users:
        await message.channel.send('UserID is already in the database.')
        return
    member = discord.utils.get(message.guild.members, id=user_id)
    if not member:
        await message.channel.send('UserID not found in the server.')
        return
    await add_excluded_user_into_database(user_id, message.author.id)
    await message.channel.send('Added **%s** into the database.' % member.name)


async def cmd_delete_excluded_user(client, message, arg):
    if not arg:
        await message.channel.send('Usage: !delexcludedduser <userID>. '
                                   'or highlight someone: !delexcludedduser @Thomaxius')
        return
    user_id = arg[:-1].lstrip('<@')
    if not user_id.isdigit():
        await message.channel.send('UserID has to be numeric.')
        return
    excluded_users = await get_excluded_users()
    if user_id not in excluded_users:
        await message.channel.send('UserID not found in the database')
        return
    member = discord.utils.get(message.guild.members, id=user_id)
    await del_excluded_user_from_database(user_id)
    await message.channel.send('Removed **%s** from the database.' % member.name)


async def get_excluded_users():
    results = await db.fetch("""
        SELECT
            excluded_user_id
        FROM
            excluded_users
        """)
    return [item['excluded_user_id'] for item in results]


async def add_excluded_user_into_database(excluded_user_id, adder_user_id):
    await db.execute("""
        INSERT INTO excluded_users AS a
        (excluded_user_id, added_by_id)
        VALUES ($1, $2)""", excluded_user_id, adder_user_id)
    log.info('Added an excluded user into the database: {0}'.format(excluded_user_id))


async def del_excluded_user_from_database(excluded_user_id):
    await db.execute("""
        DELETE
        FROM
            excluded_users
        WHERE
            excluded_user_id like $1
        """, excluded_user_id)
    log.info('Removed an excluded user from the database:'.format(excluded_user_id))


async def get_reset_date() -> datetime:
    date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if date.weekday() == 0:
        date += timedelta(1)
    while date.weekday() != 0:
        date += timedelta(1)
    return to_helsinki(as_utc(date))


async def get_time_until_reset_message() -> str:
    now = as_utc(datetime.now())
    reset_time: datetime = await get_reset_date()
    delta = reset_time - now
    template = "Time until this week's stats will be reset: {0} days, {1} hours, {2} minutes, {3} seconds"
    msg = template.format(*delta_to_tuple(delta))
    return msg


def register():
    return {
        'randomquote': cmd_randomquote,
        'whosaidit': cmd_whosaidit,
        'top': cmd_top,
        'addexcludeduser': cmd_add_excluded_user,
        'delexcludeduser': cmd_delete_excluded_user,
        'legendaryquote': cmd_legendary_quote
    }
