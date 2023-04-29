from asyncio import sleep
from util import pmap, log_exception
import database as db
import json
import logger
import util

log = logger.get("STATS")

async def task():
    statistic_funcs = [
        spammer_of_the_day,
        messages_by_weekdays,
        last_month_daily_message_counts,
        rolling_message_counts,
        messages_in_last_in_last_week_month,
    ]

    while True:
        await sleep(60)
        try:
            log.info("Calculating statistics")
            await pmap(lambda func: func(), statistic_funcs)
        except Exception:
            await log_exception(log)

async def spammer_of_the_day():
    sql = """
        SELECT
            coalesce(name, m->'author'->>'username') as spammeroftheday,
            user_id,
            count(*) as message_count
        FROM message
        JOIN discord_user USING (user_id)
        WHERE NOT bot
        AND date_trunc('day', ts) = date_trunc('day', current_timestamp)
        AND content NOT LIKE '!%'
        GROUP BY
            coalesce(name, m->'author'->>'username'),
            user_id
        ORDER BY message_count DESC
        LIMIT 1
    """
    row = await db.fetchrow(sql)
    content = dict(row) if row else None
    await upsert_statistic("SPAMMER_OF_THE_DAY", content)

async def messages_by_weekdays():
    # PostgreSQL uses 0-6 to represent days starting from sunday
    day_names = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]

    async def exec(days):
        sql = """
            WITH daily_messages AS (
                SELECT
                    date_trunc('day', ts) AS day,
                    count(*) AS messages
                FROM message
                WHERE NOT bot AND content NOT LIKE '!%'
                GROUP BY date_trunc('day', ts)
            )
            SELECT
                extract(dow FROM day)::bigint AS day_of_week,
                avg(coalesce(messages, 0))::bigint AS count
            FROM generate_series(
                date_trunc('day', current_timestamp - interval '{days} days'),
                date_trunc('day', current_timestamp),
                interval '1 day'
            ) AS day
            LEFT JOIN daily_messages USING (day)
            GROUP BY extract(dow FROM day)
            ORDER BY day_of_week
        """.format(days=days)
        rows = await db.fetch(sql)
        content = []
        for row in rows:
            content.append({
                "dayOfWeek": day_names[row["day_of_week"]],
                "messages": row["count"],
            })
        await upsert_statistic("MESSAGES_BY_WEEKDAYS_{0}D".format(days), content)

    await pmap(exec, [7, 30, 90, 360])

async def last_month_daily_message_counts():
    sql = """
        SELECT
            extract(epoch from ts::date) * 1000 as epoch,
            sum(case bot when true then 1 else 0 end) as bot_count,
            sum(case bot when false then 1 else 0 end) as user_count
        FROM message
        GROUP BY ts::date
        ORDER BY ts::date DESC
        LIMIT 30
    """
    rows = await db.fetch(sql)
    content = list(map(dict, rows))
    await upsert_statistic("LAST_MONTH_DAILY_MESSAGE_COUNTS", content)

async def rolling_message_counts():
    async def exec(days):
        sql = """
            WITH daily_count AS (
                SELECT
                    extract(epoch from ts::date) * 1000 as epoch,
                    count(*) as messages
                FROM message
                WHERE NOT bot
                GROUP BY ts::date
            )
            SELECT
                epoch::bigint,
                avg(messages) OVER (ORDER BY epoch ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)::float AS average
            FROM daily_count
            ORDER BY epoch DESC
            LIMIT {days}
        """.format(days=days)
        rows = await db.fetch(sql)
        content = list(map(dict, rows))
        await upsert_statistic("ROLLING_MESSAGE_COUNTS_{0}D".format(days), content)
    await pmap(exec, [30])

async def messages_in_last_in_last_week_month():
    async def exec(days):
        sql = """
            SELECT coalesce(sum(daily.count), 0)::bigint AS count
            FROM (
                SELECT count(*)::numeric AS count
                FROM message
                GROUP BY ts::date
                ORDER BY ts::date DESC
                LIMIT {days}
            ) AS daily
        """.format(days=days)
        row = await db.fetchrow(sql)
        content = int(row["count"])
        await upsert_statistic("MESSAGES_IN_LAST_{0}D".format(days), content)
    await pmap(exec, [7, 30])

async def upsert_statistic(statistic_id, content):
    json_string = json.dumps(content)
    log.debug("%s %s", statistic_id, json_string)
    sql = """
        INSERT INTO statistics (statistics_id, content, changed)
        VALUES ($1, $2, current_timestamp)
        ON CONFLICT (statistics_id) DO UPDATE SET
            content = EXCLUDED.content,
            changed = EXCLUDED.changed
    """
    await db.execute(sql, statistic_id, json_string)

def register(client):
    #util.start_task_thread(task())
    return {}
