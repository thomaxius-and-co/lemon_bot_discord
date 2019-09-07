from test_util import async_test, reset_db
import database as db

@async_test
async def test_reset_db():
  await reset_db()
  assert await db.fetchval("select count(*) from message") == 0

@async_test
async def test_transaction_rollback_on_exception():
  await reset_db()
  assert await count(db, "statistics") == 0
  try:
    async with db.transaction() as tx:
      await tx.execute("insert into statistics (statistics_id, content) values ('TEST_STATISTIC', '{}')")
      assert await count(tx, "statistics") == 1
      raise Exception("EXPECTED")
  except Exception as e:
    assert str(e) == "EXPECTED"
  assert await count(db, "statistics") == 0

async def count(tx, table):
  return await tx.fetchval("select count(*) from {0}".format(table))
