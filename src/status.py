import database as db
from asyncio import sleep
import discord
import logger
import corona

log = logger.get("STATUS")

CUSTOM_STATUS = None
CUSTOM_STATUS_DISPLAYED = False



async def main(client, task_name):
    task = TASKS.get(task_name, None)
    if not task:
        raise Exception('Error: Invalid task name supplied to status.py')
    await task(client)


async def corona_stats_into_status(client):
    global CUSTOM_STATUS_DISPLAYED
    while True:
        log.info("Checking and updating corona stats")
        total_infections_amount, date_last_infected, infections_today, infections_yesterday, recovered_amount, deaths_amount = await corona.get_corona_stats()
        if not CUSTOM_STATUS:
            await change_status(client, "Finland: Infected: {0} Recovered: {1} Deaths: {2}".format(total_infections_amount, recovered_amount, deaths_amount))
        await sleep(1800)



async def check_user_and_message_count(client):
    global CUSTOM_STATUS_DISPLAYED
    old_user_count, old_message_count = None, None
    while True:
        log.info("Checking user and message count")
        total_users = await get_user_count()
        total_messages = await get_message_count()
        if total_messages and ((total_users != old_user_count) or (total_messages != old_message_count)) and \
                ((not CUSTOM_STATUS) or (CUSTOM_STATUS and CUSTOM_STATUS_DISPLAYED)):
            log.info("Setting new values: %s total users, %s messages", total_users, total_messages)
            await change_status(client, ('Total users: %s | Total messages: %s' % (total_users, total_messages)))
            old_user_count, old_message_count = total_users, total_messages
            CUSTOM_STATUS_DISPLAYED = False
        elif CUSTOM_STATUS and not CUSTOM_STATUS_DISPLAYED:
            await change_status(client, CUSTOM_STATUS)
            CUSTOM_STATUS_DISPLAYED = True
        else:
            log.info("Nothing to update")
        await sleep(1800)

async def change_status(client, status):
    await client.change_presence(
        activity=discord.Game(name=status))

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

async def cmd_clearstatus(client, message, _):
    global CUSTOM_STATUS
    global CUSTOM_STATUS_DISPLAYED
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await message.channel.send('https://youtu.be/gvdf5n-zI14')
        return
    CUSTOM_STATUS = None
    CUSTOM_STATUS_DISPLAYED = None
    await client.change_presence(activity=discord.Game(name=None))

async def cmd_status(client, message, input):
    global CUSTOM_STATUS
    global CUSTOM_STATUS_DISPLAYED
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await message.channel.send('https://youtu.be/gvdf5n-zI14')
        return
    if not input:
        await message.channel.send('You need to specify a status. For example: ```!status I am online!```')
        return
    if len(input) > 128:
        await message.channel.send('Maximum allowed length for status is 128 characters.')
        return
    await client.change_presence(game=discord.Game(name=input))
    CUSTOM_STATUS = input
    CUSTOM_STATUS_DISPLAYED = True

TASKS = {
    'corona': corona_stats_into_status,
    'messages_count': check_user_and_message_count
}

def register(client):
    return {
        'status': cmd_status,
        'clearstatus': cmd_clearstatus
    }