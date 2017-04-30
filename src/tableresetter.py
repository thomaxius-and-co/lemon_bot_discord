# a Thing that resets certain tables at certain times, such as 'whosaidit' gets resetted weekly.

import database as db
import datetime

async def main():
    resetdate = await get_reset_date_from_db()
    print('next reset date:', resetdate['max'])
    if resetdate['max']:
        print('apparently there is a resetdate, maybe later we will do something instead of printing this')
        return
    if not resetdate['max']:
        await generatenewdate(nodateindb=True)
        print('No reset date in database, generating one..')

async def get_reset_date_from_db():
    async with db.connect() as c:
        return await c.fetchrow("""
            SELECT max(nextresetdate) from resetdate
            """)

async def set_reset_date_to_db(date):
    async with db.connect() as c:
        await c.execute("""
            INSERT INTO resetdate (nextresetdate) VALUES ($1);
            """, date)
        print('Reset date set: date')

async def generatenewdate(nodateindb=False):
    if nodateindb:
        newdate = (datetime.datetime.today() + datetime.timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        await set_reset_date_to_db(newdate)
