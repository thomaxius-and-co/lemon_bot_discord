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

const findUserMessageCount = () =>
  db.query('SELECT count(*)::numeric FROM message WHERE NOT bot').then(rows => Number(rows[0].count))

const findBotMessageCount = () =>
  db.query('SELECT count(*)::numeric FROM message WHERE bot').then(rows => Number(rows[0].count))

const messagesInLastNDays = days =>
  db.query(`
    SELECT sum(daily.count) AS count
    FROM (
      SELECT count(*)::numeric AS count
      FROM message
      GROUP BY ts::date
      ORDER BY ts::date DESC
      LIMIT ${Number(days)}
    ) AS daily
  `).then(rows => rows[0].count)

const findDailyMessageCounts = days =>
  db.query(`
    SELECT
      extract(epoch from ts::date) * 1000 as epoch,
      sum(case bot when true then 1 else 0 end) as bot_count,
      sum(case bot when false then 1 else 0 end) as user_count
    FROM message
    GROUP BY ts::date
    ORDER BY ts::date DESC
    LIMIT ${Number(days)}
  `)

const findRolling7DayMessageCounts = days =>
  db.query(`
    WITH daily_count AS (
      SELECT
        extract(epoch from ts::date) * 1000 as epoch,
        count(*) as messages
      FROM message
      WHERE NOT bot
      GROUP BY ts::date
    )
    SELECT
      epoch,
      avg(messages) OVER (ORDER BY epoch ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS average
    FROM daily_count
    ORDER BY epoch DESC
    LIMIT ${Number(days)}
  `)

const findSpammerOfTheDay = () =>
  db.query(`
	SELECT
            coalesce(name, m->'author'->>'username') as spammeroftheday,
            user_id,
            count(*) as message_count
	FROM 
			message
	JOIN 
			discord_user using (user_id)
    WHERE
			NOT bot 
			and date_trunc('day', ts) = date_trunc('day', current_timestamp) 
			and content not like '!%'
    GROUP BY 
			coalesce(name, m->'author'->>'username'), user_id order by message_count desc limit 1
  `).then(rows => rows[0])

  
const findMessageCountByUser = userId =>
  db.query(`SELECT count(*) FROM message WHERE user_id = $1`, userId).then(rows => rows[0].count)

const countMessagesByWeekdays = days =>
  db.query(`
    WITH daily_messages AS (
      SELECT
        date_trunc('day', ts) AS day,
        count(*) AS messages
      FROM message
      WHERE NOT bot AND content NOT LIKE '!%'
      GROUP BY date_trunc('day', ts)
    )
    SELECT
      extract(dow FROM day) AS day_of_week,
      avg(coalesce(messages, 0)) AS count
    FROM generate_series(
      date_trunc('day', current_timestamp - interval '${Number(days)} days'),
      date_trunc('day', current_timestamp),
      interval '1 day'
    ) AS day
    LEFT JOIN daily_messages USING (day)
    GROUP BY extract(dow FROM day)
    ORDER BY day_of_week
  `).then(rows => rows.map(row => {
    // PostgreSQL uses 0-6 to represent days starting from sunday
    const dayNames = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
    return {
      dayOfWeek: dayNames[row.day_of_week],
      messages: row.count,
    }
  }))

module.exports = {
  findUserMessageCount,
  findBotMessageCount,
  messagesInLastNDays,
  findDailyMessageCounts,
  findRolling7DayMessageCounts,
  findMessageCountByUser,
  findSpammerOfTheDay,
  countMessagesByWeekdays,
}
