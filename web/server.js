const Promise = require('bluebird')
const crypto = require('crypto')
const path = require('path')
const express = require('express')
const ReactDOMServer = require('react-dom/server')

const db = require('./db')
const auth = require("./auth")

const basePage = require('./pages/basePage')
const statisticsPage = require('./pages/statisticsPage')
const adminPage = require('./pages/adminPage')
const gameStatisticsPage = require('./pages/gameStatisticsPage')

const app = express()
auth.init(app)

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
    return Promise.join(
      messageCountByUser,
      db.findUserMessageCount(),
      db.findBotMessageCount(),
      db.messagesInLastNDays(7),
      db.messagesInLastNDays(30),
      db.findSpammerOfTheDay(),
      db.findLastMonthDailyMessageCounts(),
      db.findRolling7DayMessageCounts(30),
      db.countMessagesByWeekdays(7),
      db.countMessagesByWeekdays(30),
      db.countMessagesByWeekdays(90),
      db.countMessagesByWeekdays(360),
      (messageCountByUser, userMessages, botMessages, messagesInLastWeek, messagesInLastMonth, spammer, lastMonthDailyMessageCounts, rolling7DayMessageCounts, messagesPerWeekday7, messagesPerWeekday30, messagesPerWeekday90, messagesPerWeekday360) => ({
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
      })
	  ) 
  case '/gameStatisticsPage':
    return Promise.join(
      db.topBlackjack(), db.topSlots(), db.topWhosaidit(), db.whosaiditWeeklyWinners(), db.countMessagesByWeekdays,
      (topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners) => ({
        topBlackjack, topSlots, topWhosaidit, whosaiditWeeklyWinners
      })
	  )

  default:
    return Promise.resolve({})
  }
}

renderApp = (req, res, next) => {
  console.log(`Requested ${req.originalUrl}`)
  const path = req.originalUrl
  let page = undefined
  if (path === '/admin') {
    page = adminPage
  } else if (path === '/') {
    page = statisticsPage
  } else if (path === '/gameStatisticsPage') {
    page = gameStatisticsPage
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
  } else {
    next()
  }
}

app.get("/admin", auth.requireAdmin, renderApp)
app.get("/", renderApp)
app.get("/gameStatisticsPage", renderApp)

const bundleJsFilePath = path.resolve(`${__dirname}/public/bundle.js`)
app.get('/bundle.js', serveStaticResource(bundleJsFilePath))
const styleCssFilePath = path.resolve(`${__dirname}/public/style.css`)
app.get('/style.css', serveStaticResource(styleCssFilePath))
const c3CssFilePath = path.resolve(`${__dirname}/node_modules/c3/c3.min.css`)
app.get('/c3.min.css', serveStaticResource(c3CssFilePath))

process.on('SIGUSR2', () => process.exit(0))
app.listen(3000, () => {
  console.log('Listening on port 3000')
})
