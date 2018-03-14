from time_util import to_helsinki, as_utc
from lan import delta_to_tuple
from datetime import datetime, timedelta


def get_time_until_reset():
    datenow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if datenow.weekday() == 0:
        datenow += timedelta(1)
    while datenow.weekday() != 0:
        datenow += timedelta(1)
    timeuntilreset = to_helsinki(as_utc(datenow))
    now = as_utc(datetime.now())
    delta = timeuntilreset - now
    template = "Time until this week's stats will be reset: {0} days, {1} hours, {2} minutes, {3} seconds"
    msg = template.format(*delta_to_tuple(delta))
    return msg

print(get_time_until_reset())