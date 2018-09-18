const Promise = require('bluebird')
const crypto = require('crypto')
const path = require('path')
const express = require('express')
const ReactDOMServer = require('react-dom/server')

const db = require('./db')
const auth = require("./auth")
const nokia = require("./nokia")

const basePage = require('./pages/basePage')
const statisticsPage = require('./pages/statisticsPage')
const adminPage = require('./pages/adminPage')
const gameStatisticsPage = require('./pages/gameStatisticsPage')
const faceitStatisticsPage = require('./pages/faceitStatisticsPage')
const personalFaceitStatsPage = require('./pages/personalFaceitStatsPage')
const faceit_api = require('./faceit_api')
const app = express()
auth.init(app)
nokia.setup(app)

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
    const nokiaDevices = !req.user ? Promise.resolve(undefined) :
      nokia.getDevice(req.user.id)
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
      nokiaDevices,
      (messageCountByUser, userMessages, botMessages, messagesInLastWeek, messagesInLastMonth, spammer, lastMonthDailyMessageCounts, rolling7DayMessageCounts, messagesPerWeekday7, messagesPerWeekday30, messagesPerWeekday90, messagesPerWeekday360, nokiaDevices) => ({
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
        nokiaDevices,
      })
	  ) 
  case '/gameStatisticsPage':
    return Promise.join(
      db.topBlackjack(), db.topSlots(), db.topWhosaidit(), db.whosaiditWeeklyWinners(),
      (topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners) => ({
        topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners
      })
	  )
  case '/faceitStatisticsPage':
  return Promise.join(
    db.faceitTopTen(), db.getLatestFaceitEntry(), db.getEloForPast30Days(), 
    (topFaceit, latestFaceitEntry, eloForPast30Days ) => ({
      topFaceit, latestFaceitEntry, eloForPast30Days
    })
  )
  case '/personalFaceitStatsPage':
    if (isValidGetParameter(req.query.faceit_guid)) {
      return Promise.join(
        db.getPersonalWeeklyElo(req.query.faceit_guid), db.getRollingAverageElo(req.query.faceit_guid), db.getLatestFaceitEntry(), faceit_api.getStats(req.query.faceit_guid),
        (personalWeeklyElo, rollingAverageElo, latestFaceitEntry, stats) => ({
          personalWeeklyElo, rollingAverageElo, latestFaceitEntry, stats
        })
      )
    }
      return Promise.resolve({}) 
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
  } else if (path === '/gameStatisticsPage') {
    page = gameStatisticsPage
  } else if (path === '/faceitStatisticsPage') {
    page = faceitStatisticsPage
  } else if (path === '/personalFaceitStatsPage') {
    page = personalFaceitStatsPage
  }
  if (page) {
    Promise.join(
      buildInitialState(req),
      checksumPromise(bundleJsFilePath),
      checksumPromise(styleCssFilePath),
      checksumPromise(c3CssFilePath),
      (state, bundleJsChecksum, styleCssChecksum, c3CssChecksum) => {
        const initialState = Object.assign(page.initialState, state)
        const checksums = {bundleJsChecksum, styleCssChecksum, c3CssChecksum}
        res.send(ReactDOMServer.renderToString(basePage(page, initialState, checksums)))
      }
    ).catch(next)
  }
   else {
    next()
  }
}

app.get("/admin", auth.requireAdmin, renderApp)
app.get("/", renderApp)
app.get("/gameStatisticsPage", renderApp)
app.get("/faceitStatisticsPage", renderApp)
app.get("/personalFaceitStatsPage", renderApp)

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
