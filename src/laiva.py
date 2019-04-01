from datetime import datetime, timedelta
from math import floor

from time_util import as_helsinki, as_utc, to_utc

def register(client):
    return {
        "laiva": cmd_laiva,
        "laivalle": cmd_laiva,
    }

async def cmd_laiva(client, message, _):
    theme = "The laiva to start a new generation of laivas"
    laiva = to_utc(as_helsinki(datetime(2019, 6, 7, 17, 0)))
    laivaover = to_utc(as_helsinki(datetime(2019, 6, 9, 10, 30)))

    now = as_utc(datetime.now())

    if (laiva < now) and (laivaover > now):
        await client.send_message(message.channel, "Laiva is currently happening!!")
        return

    if ((laivaover + timedelta(days=1)) < now) and laiva < now:
        time_ago = delta_to_str(now - laivaover)
        await client.send_message(message.channel, f"**Last laiva ended:** {time_ago} ago, **next laiva:** TBA.")
        return

    if laivaover < now:
        await client.send_message(message.channel, "Laiva is already over, but paha olo remains.")
        return

    time_left = delta_to_str(laiva - now)
    msg = f"Time left until '{theme}': {time_left}!!"
    await client.send_message(message.channel, msg)

def delta_to_str(delta):
    return "{0} days, {1} hours, {2} minutes, {3} seconds".format(*delta_to_tuple(delta))

def delta_to_tuple(delta):
    days = delta.days
    s = delta.seconds
    seconds = s % 60
    m = floor((s - seconds) / 60)
    minutes = m % 60
    h = floor((m - minutes) / 60)
    hours = h
    return (days, hours, minutes, seconds)
