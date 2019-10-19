from datetime import datetime
from math import floor

from time_util import as_helsinki, as_utc, to_utc

def register(client):
    return {
        "lan": cmd_lan,
        "lanit": cmd_lan,
    }

def delta_to_tuple(delta):
    days = delta.days
    s = delta.seconds
    seconds = s % 60
    m = floor((s - seconds) / 60)
    minutes = m % 60
    h = floor((m - minutes) / 60)
    hours = h
    return (days, hours, minutes, seconds)

async def cmd_lan(client, message, query):
    lan = to_utc(as_helsinki(datetime(2019, 11, 22, 16, 0)))
    lan_over = to_utc(as_helsinki(datetime(2019, 11, 24, 14, 30)))
    now = as_utc(datetime.now())

    if (lan < now) and (lan_over > now):
        await message.channel.send("HelmiLAN is currently happening!!")
        return

    if lan < now:
        await message.channel.send("HelmiLAN is already over but väsymys remains.")
        return

    delta = lan - now
    template = "Time until HelmiLAN: {0} days, {1} hours, {2} minutes, {3} seconds"
    msg = template.format(*delta_to_tuple(delta))
    await message.channel.send(msg)
