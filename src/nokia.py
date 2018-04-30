import command
import emoji
import logger
import nokia_api as api
from nokia_api import AccountNotLinkedException

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
    try:
        devices = await api.getdevice(user_id)
        await client.send_message(message.channel, str(devices))
    except AccountNotLinkedException:
        await client.send_message(message.channel, "Please link your Nokia Health account")


def register(client):
    return {
        "nokia": cmd_nokia,
    }
