const Promise = require('bluebird')
const pgp = require('pg-promise')({ promiseLib: Promise })
const {distinct} = require('./util.js')

const connectionDetails = {
  host:     process.env.DATABASE_HOST,
  port:     process.env.DATABASE_PORT,
  database: process.env.DATABASE_NAME,
  user:     process.env.DATABASE_USERNAME,
  password: process.env.DATABASE_PASSWORD,
  // After 75 connections used by the bot we have 25 connections left for the website
  min: 5,
  max: 25,
}

const db = pgp(connectionDetails)

const findUserMessageCount = () =>
  db.query('SELECT count(*)::numeric FROM message WHERE NOT bot').then(rows => Number(rows[0].count))

const findBotMessageCount = () =>
  db.query('SELECT count(*)::numeric FROM message WHERE bot').then(rows => Number(rows[0].count))

const messagesInLastWeek = () =>
  fetchPrecalculatedStatistics("MESSAGES_IN_LAST_7D")

const messagesInLastMonth = () =>
  fetchPrecalculatedStatistics("MESSAGES_IN_LAST_30D")

const findLastMonthDailyMessageCounts = days =>
  fetchPrecalculatedStatistics("LAST_MONTH_DAILY_MESSAGE_COUNTS")

const findRolling7DayMessageCounts = days =>
  fetchPrecalculatedStatistics(`ROLLING_MESSAGE_COUNTS_${Number(days)}D`)

const findSpammerOfTheDay = () =>
  fetchPrecalculatedStatistics("SPAMMER_OF_THE_DAY")

const fetchPrecalculatedStatistics = statisticsId =>
  db.query(`SELECT content FROM statistics WHERE statistics_id = $1`, statisticsId)
    .then(rows => rows[0] ? rows[0].content : null)
  
const findMessageCountByUser = userId =>
  db.query(`SELECT count(*) FROM message WHERE user_id = $1`, userId).then(rows => rows[0].count)

const topBlackjack = () =>
  db.query(`
	SELECT
            (wins_bj / (wins_bj + losses_bj)) * 100 as winpercentage,
            wins_bj,
            wins_bj + losses_bj as total_games,
            name,
            losses_bj,
            surrenders,
            ties,
            moneyspent_bj,
            moneywon_bj,
            concat('#', row_number() OVER (ORDER BY  (wins_bj / (wins_bj + losses_bj)) * 100 desc)) AS rank
        FROM casino_stats
        JOIN discord_user USING (user_id)
        WHERE (wins_bj + losses_bj) > 1
        ORDER BY (wins_bj / (wins_bj + losses_bj)) * 100 DESC
        LIMIT 10
  `)
  
const topSlots = () =>
  db.query(`
	SELECT
            name,
            concat('#', row_number() OVER (ORDER BY  (moneywon_slots - moneyspent_slots)desc)) AS rank,
            wins_slots + losses_slots AS total,
            wins_slots,
            losses_slots,
            moneyspent_slots,
            moneywon_slots,
            moneywon_slots - moneyspent_slots as profit,
            (wins_slots / (wins_slots + losses_slots)) * 100 AS percentage
        FROM casino_stats
        JOIN discord_user USING (user_id)
        WHERE (wins_slots + losses_slots) > 100
        ORDER BY moneywon_slots - moneyspent_slots DESC
        LIMIT 10
  `)

const topWhosaidit = () =>
  db.query(`
    with score as (
            select
                user_id,
                sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
                sum(case playeranswer when 'wrong' then 1 else 0 end) as losses
              from whosaidit_stats_history
              where date_trunc('week', time) = date_trunc('week', current_timestamp)
              group by user_id)
            select
                wins::float / (wins + losses) * 100 as ratio,
                least(0.20 * wins, 20) as bonuspct,
                wins,
                wins + losses as total,
                name,
                concat('#', row_number() OVER (ORDER BY (wins::float / (wins + losses) * 100)+ least(0.20* wins, 20) desc)) AS rank
            from score
            join discord_user using (user_id)
            where (wins + losses) >= 20
            order by rank asc
			limit 10
  `)
  
const whosaiditWeeklyWinners = () =>
  db.query(`
    -- week_score = score per pelaaja per viikko
        with week_score as (
          select
            date_trunc('week', time) as dateadded,
            user_id,
            sum(case playeranswer when 'correct' then 1 else 0 end) as wins,
            sum(case playeranswer when 'wrong' then 1 else 0 end) as losses,
            -- accuracy
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) as accuracy,
            -- bonus
            least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as bonus,
            -- score = accuracy + bonus
            100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count(*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20) as score,
            -- MAGIC! weeks_best_score on kyseisen viikon paras score
            max(100.0 * sum(case playeranswer when 'correct' then 1 else 0 end) / count (*) + least(20.0, sum(case playeranswer when 'correct' then 1 else 0 end) * 0.20)) over (partition by date_trunc('week', time)) as weeks_best_score,
            -- more magic
            count(user_id) over (partition by date_trunc('week', time)) as players
          from whosaidit_stats_history
          group by user_id, date_trunc('week', time)
          having count(*) >= 20
        )

        select dateadded, name, score, wins, losses, accuracy, bonus, players, wins + losses as total
        from week_score
        join discord_user using (user_id)
        -- Valitaan vain rivit, joilla score on viikon paras score, eli voittajat
          where not date_trunc('week', dateadded) = date_trunc('week', current_timestamp) and score = weeks_best_score and players >= 2
        order by dateadded desc
  `)    

const faceitTopTen = () =>
db.query(`
  WITH 
    last_month_elo as 
  (
      SELECT DISTINCT ON
          (faceit_guid) faceit_guid, 
          faceit_elo as last_month_elo
      FROM 
          faceit_live_stats
      WHERE
          changed >= (current_timestamp - interval '30 days')
      GROUP BY
          faceit_guid, last_month_elo, changed
      ORDER BY 
          faceit_guid, changed asc
  ),
      last_week_elo as 
    (
        SELECT DISTINCT ON
            (faceit_guid) faceit_guid, 
            faceit_elo as last_week_elo
        FROM 
            faceit_live_stats
        WHERE
            changed >= (current_timestamp - interval '7 days')
        GROUP BY
            faceit_guid, last_week_elo, changed
        ORDER BY 
            faceit_guid, changed asc
    ),
    current_elo as 
    (
        SELECT DISTINCT ON
            (faceit_guid) faceit_guid, 
            faceit_elo as current_elo,
            faceit_ranking as current_ranking
        FROM 
            faceit_live_stats
        WHERE
            changed <= current_timestamp
        GROUP BY
            faceit_guid, current_elo, changed, faceit_ranking
        ORDER BY 
            faceit_guid, changed desc

    ),      
      best_score as
    (
        SELECT 
            faceit_guid, 
            max(faceit_elo) as best_score
        FROM 
            faceit_live_Stats
        GROUP BY 
            faceit_guid
        ORDER BY max(faceit_elo)
    ),
    latest_entry as
    (
        SELECT 
            max(changed) as latest_entry,
            faceit_guid
        FROM 
            faceit_live_Stats 
        GROUP BY
            faceit_guid
          )    
    SELECT 
      faceit_guid, 
      current_elo,
      current_ranking,
      coalesce(current_elo - last_month_elo, 0) as difference_month,
      coalesce(current_elo - last_week_elo, 0) as difference_week,
      faceit_nickname as name,
      best_score,
      latest_entry
    FROM 
      current_elo
    JOIN 
      faceit_player USING  (faceit_guid)
    JOIN 
      latest_entry USING  (faceit_guid)
    LEFT JOIN
      last_week_elo USING (faceit_guid)
    LEFT JOIN
      last_month_elo USING (faceit_guid)              
    LEFT JOIN
      best_score USING (faceit_guid)
    WHERE
      faceit_guid in (select faceit_guid from faceit_guild_ranking)
    ORDER BY 
      current_ranking ASC
  `)
  .then(rows => rows.map(convertTopListTypes))

const convertTopListTypes = row =>
  Object.assign({}, row, {
    current_elo: Number(row.current_elo),
    current_ranking: Number(row.current_ranking),
    best_score: Number(row.best_score),
    difference_month: Number(row.difference_month),
    difference_week: Number(row.difference_week),
  })

const getLatestFaceitEntry = () =>
  db.query(`SELECT max(changed) as latest_entry FROM faceit_live_Stats`).then(rows => rows[0])

async function getEloForPast30Days() {
  const elos = await db.query(`
  SELECT
    distinct on (faceit_guid, date_trunc('day', changed))
    date_trunc('day', changed) as day,
    faceit_guid,
    faceit_elo as elo
  FROM 
    faceit_live_stats
  WHERE 
    changed > current_timestamp - interval '1 month'
  AND 
    faceit_guid IN 
      (
        SELECT 
          faceit_guid 
        FROM 
          faceit_guild_ranking)
  ORDER BY 
    date_trunc('day', changed), faceit_guid, changed desc
  `)
  const playerIds = distinct(elos.map(s => s.faceit_guid))
  const playerNames = await getPlayerNames(playerIds)
  return elos.map(assignName(playerNames))
}

async function getPersonalWeeklyElo(guid) {
  const elos = await db.query(`
      SELECT
      distinct on (date_trunc('week',changed))
      changed,
      concat(date_part('week', changed),'/',date_part('year', changed)) as week,
      faceit_live_stats.faceit_guid,
      faceit_elo as elo,
      faceit_nickname
    FROM 
      faceit_live_stats
    JOIN 
        faceit_player on faceit_live_stats.faceit_guid = faceit_player.faceit_guid
    WHERE 
        faceit_live_stats.faceit_guid IN 
      (
        SELECT 
          faceit_guid 
        FROM 
          faceit_guild_ranking)
    AND
        faceit_live_stats.faceit_guid = $1
    GROUP BY 
        changed, date_trunc('week', changed), faceit_live_stats.faceit_guid, concat(date_part('week', changed),'/',date_part('year', changed)), faceit_nickname, faceit_elo
    ORDER BY
        date_trunc('week',changed), changed
        DESC
  `, guid)
  return elos
}

async function getRollingAverageElo(player_guid) {
  const elos = await db.query(`
    WITH a as 
      (
        SELECT
          distinct on (date_trunc('week',changed))
          changed,
          concat(date_part('week', changed),'/',date_part('year', changed)) as week,
          faceit_live_stats.faceit_guid,
          faceit_elo as elo,
          faceit_nickname
        FROM 
          faceit_live_stats
        JOIN 
            faceit_player on faceit_live_stats.faceit_guid = faceit_player.faceit_guid
        WHERE 
            faceit_live_stats.faceit_guid IN 
          (
            SELECT 
              faceit_guid 
            FROM 
              faceit_guild_ranking)
        AND
            faceit_live_stats.faceit_guid = $1
        GROUP BY 
            changed, date_trunc('week', changed), faceit_live_stats.faceit_guid, concat(date_part('week', changed),'/',date_part('year', changed)), faceit_nickname, faceit_elo
        ORDER BY
            date_trunc('week',changed), changed
        DESC
      )
    SELECT
        week,
        faceit_guid,
        faceit_nickname,
        avg(elo) OVER (ORDER BY changed desc ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)::float AS average
    FROM
        a
    ORDER BY 
        changed
  `, player_guid)
  return elos
}

async function getAvailableWhosaiditUsers(guildId) {
  const playerIdsAndNames = await db.query(`
      SELECT
          user_id,
          coalesce(name, m->'author'->>'username') AS name
      FROM 
          message 
      JOIN 
          discord_user USING (user_id)
      WHERE
          guild_id = $1 
          AND NOT bot
          AND length(content) > 12 
          AND content NOT LIKE '!%%' 
          AND content NOT LIKE '%wwww%'
          AND content NOT LIKE '%http%' 
          AND content NOT LIKE '%.com%' 
          AND content NOT LIKE '%.fi%'
          AND content ~* '^[A-ZÅÄÖ]'
          AND NOT EXISTS (SELECT * FROM excluded_users WHERE excluded_user_id = user_id)
      GROUP BY 
          user_id, coalesce(name, m->'author'->>'username')
      ORDER BY
          random()
      LIMIT 
          5
  `, guildId)
  return playerIdsAndNames
}

async function saveLegendaryQuote(messageid, userid) {
  return await db.query(`
    INSERT INTO
        legendary_quotes
        (message_id, added_by)
    VALUES 
        ($1, $2)
    `, [String(messageid), String(userid)]).then(() => {
      console.log(`User ${userid} added a legendary quote ${messageid} into the database`) 
      return true
    }).catch((error) => {
      console.log(error.error)
      return false
    })
}

async function getQuoteForWhosaidit(guildid, userids) {
  userids = userids.map((userid) => (userid != userids[userids.length - 1]) ? `user_id = '${userid}' OR` : `user_id = '${userid}'`).join(' ') // Add OR after userid, unless userid is last element in the list
  const quotes = await db.query(`
  SELECT
      content,
      coalesce(name, m->'author'->>'username') as username,
      user_id,
      m->'mentions',
      message_id,
      ts
  FROM 
      message 
  JOIN 
      discord_user USING (user_id)
  WHERE
  (${userids})
      AND guild_id = ${guildid}
      AND length(content) > 12
      AND length(content) < 1000 
      AND content NOT LIKE '!%%' 
      AND content NOT LIKE '%wwww%'
      AND content NOT LIKE '%http%' 
      AND content NOT LIKE '%.com%' 
      AND content NOT LIKE '%.fi%'
      AND content ~* '^[A-ZÅÄÖ]'
      AND NOT bot 
  ORDER BY 
      random()
  LIMIT 
      15
      `) 

  return quotes
}

async function getUserNamesAndIds() {
  return await db.query(`
  SELECT
        user_id, name
  FROM
        discord_user
  `)
}

async function saveWhosaiditHistory(userid, message_id, sanitizedquestion, correctname, answer) {
    correct = correctname == answer
    return await db.query(`
        INSERT INTO whosaidit_stats_history
        (user_id, message_id, quote, correctname, playeranswer, correct, time, week)
        VALUES ($1, $2, $3, $4, $5, $6, now(), date_part('week', localtimestamp))
    `, [userid, message_id, sanitizedquestion, correctname, correct ? 'correct' : 'wrong', correct ? 1 : 0]).then(() => console.log(`Saved whosaidit game result for ${userid}`))
    // Originally this was made using the 'wrong' and 'correct' strings, which is wrong and was later fixed to be 0 for wrong and 1 for correct. Here we add both cause I'm lazy to implement the new thing now.
}

async function getPlayerNames(playerIds) {
  const rows = await db.query(`SELECT faceit_guid, faceit_nickname FROM faceit_player WHERE faceit_guid = ANY ($1)`, [playerIds])
  const pairs = rows.map(r => [r.faceit_guid, r.faceit_nickname])
  return pairsToObject(pairs)
}

function assignName(nameMap) {
  return obj => Object.assign({}, obj, {faceit_nickname: nameMap[obj.faceit_guid]})
}

// Transforms [[a, b], [c, d]] to {a: b, c: d}
function pairsToObject(pairs) {
  let obj = {}
  for (const [k, v] of pairs) {
    obj[k] = v
  }
  return obj
}

const countMessagesByWeekdays = days =>
  fetchPrecalculatedStatistics(`MESSAGES_BY_WEEKDAYS_${Number(days)}D`)

module.exports = {
  db: db,
  findUserMessageCount,
  findBotMessageCount,
  messagesInLastWeek,
  messagesInLastMonth,
  findLastMonthDailyMessageCounts,
  findRolling7DayMessageCounts,
  getEloForPast30Days,
  findMessageCountByUser,
  findSpammerOfTheDay,
  countMessagesByWeekdays,
  topSlots,
  topBlackjack,
  topWhosaidit,
  whosaiditWeeklyWinners,
  faceitTopTen,
  getLatestFaceitEntry,
  getPersonalWeeklyElo,
  getRollingAverageElo,
  getAvailableWhosaiditUsers,
  getQuoteForWhosaidit,
  saveWhosaiditHistory,
  getUserNamesAndIds,
  saveLegendaryQuote
}

