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
    ]

    while True:
        await sleep(60)
        try:
            log.info("Calculating statistics")
            for func in statistic_funcs:
                await func()
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

    for days in [7, 30, 90, 360]:
        await exec(days)

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
    util.start_task_thread(task())
    return {}
