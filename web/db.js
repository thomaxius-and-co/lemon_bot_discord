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

const findMessageCount = (req, res) =>
  db.query('SELECT count(*)::numeric FROM message').then(rows => rows[0].count)

module.exports = {
  findMessageCount,
}
