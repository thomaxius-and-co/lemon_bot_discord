const Promise = require('bluebird')
const pgp = require('pg-promise')({ promiseLib: Promise })

const connectionDetails = {
  host:     'localhost',
  port:     5432,
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
            faceit_elo as last_month_elo,
            faceit_ranking as last_month_ranking
        FROM 
            faceit_live_stats
        WHERE
            date_part('month', changed) = date_part('month', current_timestamp)
        GROUP BY
            faceit_guid, last_month_elo, last_month_ranking, changed            
        ORDER BY 
            faceit_guid, changed desc
    ),
    last_week_elo as 
    (
        SELECT DISTINCT ON
            (faceit_guid) faceit_guid, 
            faceit_elo as last_week_elo,
            faceit_ranking as last_week_ranking
        FROM 
            faceit_live_stats
        WHERE
            date_part('week', changed) = date_part('week', current_timestamp) 
        GROUP BY
            faceit_guid, last_week_elo, last_week_ranking, changed
        ORDER BY 
            faceit_guid, changed desc
    ),    
      current_elo as 
    (
        SELECT DISTINCT ON
            (faceit_guid) faceit_guid, 
            faceit_elo as current_elo,
            faceit_ranking as current_ranking
        FROM 
            faceit_live_stats
        GROUP BY
            faceit_guid, current_elo, current_ranking, changed    
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
    ) 
    SELECT 
      faceit_guid, 
      current_elo,
      current_ranking,
      current_elo - last_month_elo as difference_month,
      current_elo - last_week_elo as difference_week,
      faceit_nickname as name,
      best_score,
      concat('#', row_number() OVER (ORDER BY current_ranking asc)) AS rank
    FROM 
      current_elo
    JOIN 
      faceit_player USING  (faceit_guid)
    LEFT JOIN
      last_month_elo USING (faceit_guid)
    LEFT JOIN
      last_week_elo USING (faceit_guid)
    LEFT JOIN
      best_score USING (faceit_guid)
    ORDER BY 
      current_ranking ASC
`)  

const countMessagesByWeekdays = days =>
  fetchPrecalculatedStatistics(`MESSAGES_BY_WEEKDAYS_${Number(days)}D`)

module.exports = {
  findUserMessageCount,
  findBotMessageCount,
  messagesInLastWeek,
  messagesInLastMonth,
  findLastMonthDailyMessageCounts,
  findRolling7DayMessageCounts,
  findMessageCountByUser,
  findSpammerOfTheDay,
  countMessagesByWeekdays,
  topSlots,
  topBlackjack,
  topWhosaidit,
  whosaiditWeeklyWinners,
  faceitTopTen
}
