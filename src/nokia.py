import json
import os

import command
import database as db
import emoji
import logger
import nokia_api as api

log = logger.get("NOKIA")

async def cmd_nokia(client, message, arg):
    subcommands = {
        "devices": cmd_nokia_devices,
    }

    cmd, arg = command.parse(arg, prefix="")
    handler = subcommands.get(cmd, None)
    if handler is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return
    await handler(client, message, arg)

async def cmd_nokia_devices(client, message, arg):
    user_id = message.author.id
    row = await db.fetchrow("SELECT access_token, refresh_token FROM nokia_health_link WHERE user_id = $1", user_id)
    if row is None:
        # Nokia Health account not linked
        return

    access_token = row["access_token"]
    refresh_token = row["refresh_token"]
    devices = await api.getdevice(user_id, access_token, refresh_token)
    await client.send_message(message.channel, str(devices))

def register(client):
    return {
        "nokia": cmd_nokia,
    }
