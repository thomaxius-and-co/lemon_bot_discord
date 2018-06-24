import asyncio
import functools

import database as db

def async_test(task):
  @functools.wraps(task)
  def wrap(*args, **kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task(*args, **kwargs))
  return wrap

async def reset_db():
    async with db.transaction() as tx:
        await clear_schema(tx, "public")

async def clear_schema(tx, schema):
  for table in await get_tables(tx, schema):
    print("Dropping table {0}".format(table))
    await tx.execute("drop table if exists {0} cascade".format(table))

  with open("./sql/{0}.sql".format(schema)) as f:
    print("Initializing database")
    await tx.execute(f.read())

async def get_tables(tx, schema):
  sql = "select table_name from information_schema.tables where table_schema = $1"
  return map(lambda r: r["table_name"], await tx.fetch(sql, schema))
