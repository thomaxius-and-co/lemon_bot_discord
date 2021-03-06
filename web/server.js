const Promise = require('bluebird')
const crypto = require('crypto')
const path = require('path')
const express = require('express')
const ReactDOMServer = require('react-dom/server')
const db = require('./db')
const auth = require("./auth")
const withings = require("./withings")
const bodyParser = require('body-parser')
const basePage = require('./pages/basePage')
const statisticsPage = require('./pages/statisticsPage')
const adminPage = require('./pages/adminPage')
const gameStatisticsPage = require('./pages/gameStatisticsPage')
const faceitStatisticsPage = require('./pages/faceitStatisticsPage')
const personalFaceitStatsPage = require('./pages/personalFaceitStatsPage')
const whosaiditPage = require('./pages/whosaiditPage')
const quotesPage = require('./pages/quotesPage')
const whosaidit = require('./whosaidit')
const faceit_api = require('./faceit_api')
const app = express()
auth.init(app)
if (withings.enabled) {
  withings.setup(app)
}


const checksumPromise = filePath => new Promise((resolve, reject) => {
  require('fs').readFile(filePath, (error, fileContent) => {
    if (error) {
      reject(error)
    } else {
      resolve(crypto.createHash('md5').update(fileContent).digest('hex'))
    }
  })
})



const serveStaticResource = filePath => (req, res, next) => {
  checksumPromise(filePath).then(checksum => {
    if (req.query.checksum == checksum) {
      const oneYearInSeconds = 60 * 60 * 24 * 356
      res.setHeader('Cache-Control', `public, max-age=${oneYearInSeconds}, immutable`)
      res.sendFile(filePath)
    } else {
      res.status(404).end()
    }
  })
    .catch(next)
}

const buildInitialState = req => {
  switch (req.path) {
    case '/admin':
      return Promise.resolve({
        user: req.user,
      })
    case '/':
      const messageCountByUser = req.user ? db.findMessageCountByUser(req.user.id) : Promise.resolve(-1)
      const withingsDevices = req.user && withings.enabled ? withings.getDevice(req.user.id) : Promise.resolve(undefined)
      return Promise.join(
        messageCountByUser,
        db.findUserMessageCount(),
        db.findBotMessageCount(),
        db.messagesInLastWeek(),
        db.messagesInLastMonth(),
        db.findSpammerOfTheDay(),
        db.findLastMonthDailyMessageCounts(),
        db.findRolling7DayMessageCounts(30),
        db.countMessagesByWeekdays(7),
        db.countMessagesByWeekdays(30),
        db.countMessagesByWeekdays(90),
        db.countMessagesByWeekdays(360),
        withingsDevices,
        (messageCountByUser, userMessages, botMessages, messagesInLastWeek, messagesInLastMonth, spammer, lastMonthDailyMessageCounts, rolling7DayMessageCounts, messagesPerWeekday7, messagesPerWeekday30, messagesPerWeekday90, messagesPerWeekday360, withingsDevices) => ({
          user: req.user,
          messageCountByUser,
          userMessages,
          botMessages,
          messagesInLastWeek,
          messagesInLastMonth,
          spammer,
          lastMonthDailyMessageCounts,
          rolling7DayMessageCounts,
          messagesPerWeekday7,
          messagesPerWeekday30,
          messagesPerWeekday90,
          messagesPerWeekday360,
          withingsDevices,
        })
      )
    case '/gamestatistics':
      return Promise.join(
        db.topBlackjack(), db.topSlots(), db.topWhosaidit(), db.whosaiditWeeklyWinners(),
        (topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners) => ({
          topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners
        })
      )
    case '/faceitstatistics':
      return Promise.join(
        db.faceitTopTen(), db.getLatestFaceitEntry(), db.getEloForPast30Days(),
        (topFaceit, latestFaceitEntry, eloForPast30Days) => ({
          topFaceit, latestFaceitEntry, eloForPast30Days
        })
      )
    case '/personalfaceitstats':
      if (isValidGetParameter(req.query.faceit_guid)) {
        return Promise.join(
          db.getPersonalWeeklyElo(req.query.faceit_guid), db.getRollingAverageElo(req.query.faceit_guid), db.getLatestFaceitEntry(), faceit_api.getStats(req.query.faceit_guid), faceit_api.getPlayerDetails(req.query.faceit_guid),
          (personalWeeklyElo, rollingAverageElo, latestFaceitEntry, stats, playerDetails) => ({
            personalWeeklyElo, rollingAverageElo, latestFaceitEntry, stats, playerDetails
          })
        )
      }
    case '/whosaidit':
      return Promise.join(
        db.topWhosaidit(),
        (topWhosaidit) => ({
          topWhosaidit,
          user: req.user,
        })
      )
    case '/quotes':
      return Promise.join(
        db.getSensibleQuotes(),
        (sensibleQuotes) => ({
          user: req.user, sensibleQuotes,
        })
      )
    default:
      return Promise.resolve({})
  }
}

const isValidGetParameter = (parameter) => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.exec(parameter) // check if get parameter is a guid

renderApp = async (req, res, next) => {
  console.log(`Requested ${req.originalUrl}`)
  const path = req.path
  let page = undefined
  if (path === '/admin') {
    page = adminPage
  } else if (path === '/') {
    page = statisticsPage
  } else if (path === '/gamestatistics') {
    page = gameStatisticsPage
  } else if (path === '/faceitstatistics') {
    page = faceitStatisticsPage
  } else if (path === '/personalfaceitstats') {
    page = personalFaceitStatsPage
  } else if (path === '/whosaidit') {
    page = whosaiditPage
  } else if (path === '/quotes') {
    page = quotesPage
  }
  if (page) {
    Promise.join(
      buildInitialState(req),
      checksumPromise(bundleJsFilePath),
      checksumPromise(styleCssFilePath),
      checksumPromise(c3CssFilePath),
      (state, bundleJsChecksum, styleCssChecksum, c3CssChecksum) => {
        const initialState = Object.assign(page.initialState, state)
        const checksums = { bundleJsChecksum, styleCssChecksum, c3CssChecksum }
        res.send(ReactDOMServer.renderToString(basePage(page, initialState, checksums)))
      }
    ).catch(next)
  }
  else {
    next()
  }
}

getATableForThisMan = (req, res, next) => {
  Promise.join(
    db.topWhosaidit(),
    (topWhosaidit) => ({
      topWhosaidit
    })).then((result) => res.send({ table: result.topWhosaidit }))

}


const isValidMessageId = (messageId) => Number.isInteger(parseInt(messageId)) && messageId.length === 18

async function bulkAddLegendaryQuotes(req, res, next) {
  const { messageIds, user } = req.body.params
  if (!messageIds.filter(_messageId => !isValidMessageId(_messageId))) {
    // mutsis
    res.sendStatus(400);
  }
  for (let _messageId of messageIds) {
    await db.saveLegendaryQuote(_messageId, user.id)
    console.log(`Legendary quote ${_messageId} saved by user ${user.username}`)
  }


}


app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))
app.get("/admin", auth.requireAdmin, renderApp)
app.get("/", renderApp)
app.get("/gamestatistics", renderApp)
app.get("/faceitstatistics", renderApp)
app.get("/personalfaceitstats", renderApp)
app.get("/whosaidit", auth.requirePlayingClearance, renderApp)
app.get("/quotes", auth.requirePlayingClearance, renderApp)
app.post("/whosaidit", whosaidit.handleWhosaidit)
app.post("/answerCheck", whosaidit.checkAnswer)
app.post("/addResult", whosaidit.addResult)
app.post("/getTable", getATableForThisMan)
app.post("/addLegendaryQuote", whosaidit.addLegendaryQuote)
app.post("/bulkAddLegendaryQuotes", auth.requirePlayingClearance, bulkAddLegendaryQuotes)

const bundleJsFilePath = path.resolve(`${__dirname}/public/bundle.js`)
app.get('/bundle.js', serveStaticResource(bundleJsFilePath))
const styleCssFilePath = path.resolve(`${__dirname}/public/style.css`)
app.get('/style.css', serveStaticResource(styleCssFilePath))
const c3CssFilePath = path.resolve(`${__dirname}/node_modules/c3/c3.min.css`)
app.get('/c3.min.css', serveStaticResource(c3CssFilePath))

process.on('SIGUSR2', () => process.exit(0))
process.on('SIGINT', () => process.exit(0))

app.listen(3000, () => {
  console.log('Listening on port 3000')
})
