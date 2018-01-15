from datetime import datetime, timedelta
from math import floor

from time_util import as_helsinki, as_utc, to_utc

def register(client):
    return {
        "valokuitu": cmd_valokuitu,
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

async def cmd_valokuitu(client, message, query):
    valokuitu = (datetime.now().replace(hour=12, minute=00) + timedelta(days=1))
    now = as_utc(datetime.now())

    delta = valokuitu - now
    template = "Valokuitu will be installed in: {0} days, {1} hours, {2} minutes, {3} seconds."
    msg = template.format(*delta_to_tuple(delta))
    await client.send_message(message.channel, msg)

