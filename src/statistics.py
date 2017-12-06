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
