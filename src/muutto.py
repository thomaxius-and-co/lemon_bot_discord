from datetime import datetime, timedelta
from math import floor

from time_util import as_helsinki, as_utc, to_utc

def register(client):
    return {
        "muutto": cmd_muutto,
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

async def cmd_muutto(client, message, query):
    muutto = to_utc(as_helsinki(datetime(2018, 3, 29, 12, 0)))
    muuttoover = to_utc(as_helsinki(datetime(2018, 3, 30, 12, 0)))
    now = as_utc(datetime.now())
    now_to_last_muuttoover = now - muuttoover

    if (muutto < now) and (muuttoover > now):
        await client.send_message(message.channel, "Muutto is currently happening!! (probably)")
        return

    if ((muuttoover + timedelta(days=4)) < now) and muutto < now:
        await client.send_message(message.channel, ("**Muutto ended:** {0} days, {1} hours, {2} minutes, {3} seconds ago, **next muutto:** TBA.")
                                  .format(*delta_to_tuple(now_to_last_muuttoover)))
        return

    if muuttoover < now:
        await client.send_message(message.channel, "Muutto is over, but infernal tuparit are still coming!!")
        return

    delta = muutto - now
    template = "Time left until muutto: {0} days, {1} hours, {2} minutes, {3} seconds!!"
    msg = template.format(*delta_to_tuple(delta))
    await client.send_message(message.channel, msg)

