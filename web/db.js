const Promise = require('bluebird')
const pgp = require('pg-promise')({ promiseLib: Promise })

const connectionDetails = {
  host:     'localhost',
  port:     5432,
  database: process.env.DATABASE_NAME,
  user:     process.env.DATABASE_USERNAME,
  password: process.env.DATABASE_PASSWORD,
}

const db = pgp(connectionDetails)

const findMessageCount = () =>
  db.query('SELECT count(*)::numeric FROM message').then(rows => rows[0].count)

const messagesInLastNDays = n =>
  db.query(`SELECT count(*)::numeric FROM message WHERE ts > (current_timestamp - interval '${Number(n)} days')`).then(rows => rows[0].count)

const findDailyMessageCounts = days =>
  db.query(`
    SELECT extract(epoch from ts::date) as epoch, count(*) as count
    FROM message
    GROUP BY ts::date
    ORDER BY ts::date DESC
    LIMIT ${Number(days)}
  `)

module.exports = {
  findMessageCount,
  messagesInLastNDays,
  findDailyMessageCounts,
}
