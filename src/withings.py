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
        await message.add_reaction(emoji.CROSS_MARK)
        return
    await handler(client, message, arg)

async def cmd_withings_devices(client, message, arg):
    user_id = message.author.id
    try:
        devices = await api.getdevice(user_id)
        await message.channel.send(str(devices))
    except AccountNotLinkedException:
        await message.channel.send("Please link your Withings account")

def register(client):
    return {
        "nokia": cmd_withings,
        "withings": cmd_withings,
    }
