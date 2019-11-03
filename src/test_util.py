from contextlib import contextmanager
from operator import itemgetter
import asyncio
import functools
import os

import database as db
import migration

def async_test(task):
  @functools.wraps(task)
  def wrap(*args, **kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task(*args, **kwargs))
  return wrap

async def reset_db():
    async with db.transaction() as tx:
        await clear_schema(tx, "public")
        await set_latest_migration_version(tx)


async def set_latest_migration_version(tx):
  migrations = migration.find_migrations()
  latest_version = max(map(itemgetter(0), migrations))
  await migration.init_migration_table(tx)
  await migration.insert_version(tx, latest_version)

async def clear_schema(tx, schema):
  print("Initializing database")
  for table in await get_tables(tx, schema):
    await tx.execute("drop table if exists {0} cascade".format(table))

  with open("./sql/{0}.sql".format(schema)) as f:
    await tx.execute(f.read())

async def get_tables(tx, schema):
  sql = "select table_name from information_schema.tables where table_schema = $1"
  return map(lambda r: r["table_name"], await tx.fetch(sql, schema))

@contextmanager
def env(key, value):
    original = os.environ.get(key, None)
    try:
        os.environ[key] = value
        yield
    finally:
        if original is None:
            del os.environ[key]
        else:
            os.environ[key] = original
