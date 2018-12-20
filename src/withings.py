import command
import emoji
import logger
import withings_api as api
from withings_api import AccountNotLinkedException

log = logger.get("WITHINGS")

async def cmd_withings(client, message, arg):
    subcommands = {
        "devices": cmd_withings_devices,
    }

    cmd, arg = command.parse(arg, prefix="")
    handler = subcommands.get(cmd, None)
    if handler is None:
        await client.add_reaction(message, emoji.CROSS_MARK)
        return
    await handler(client, message, arg)

async def cmd_withings_devices(client, message, arg):
    user_id = message.author.id
    try:
        devices = await api.getdevice(user_id)
        await client.send_message(message.channel, str(devices))
    except AccountNotLinkedException:
        await client.send_message(message.channel, "Please link your Withings account")

def register(client):
    return {
        "nokia": cmd_withings,
        "withings": cmd_withings,
    }