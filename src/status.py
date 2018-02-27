import database as db
from asyncio import sleep
import discord
import logger

log = logger.get("STATUS")


async def main(client):
    await check_user_and_message_count(client)

async def check_user_and_message_count(client):
    old_user_count, old_message_count = None, None
    while True:
        log.info("Checking user and message count")
        total_users = await get_user_count()
        total_messages = await get_message_count()
        if total_messages and ((total_users != old_user_count) or (total_messages != old_message_count)):
            await change_status(client, total_users, total_messages)
            old_user_count, old_message_count = total_users, total_messages
        else:
            log.info("Nothing to update")
        await sleep(3600)

async def change_status(client, total_users, total_messages):
    log.info("Setting new values: %s total users, %s messages" % (total_users, total_messages))
    await client.change_presence(
        game=discord.Game(name='Total users: %s | Total messages: %s' % (total_users, total_messages)))

async def get_user_count():
    result = await db.fetchrow("""
        select 
            count(*) 
        from 
            discord_user
    """)
    if result:
        return result['count']
    else:
        return None

async def get_message_count():
    result = await db.fetchrow("""
        select 
            count(*) 
        from 
            message
    """)
    if result:
        return result['count']
    else:
        return None

def register(client):
    return {
    }