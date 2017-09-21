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
      db.findDailyMessageCounts(30),
      (messageCountByUser, userMessages, botMessages, messagesInLastWeek, messagesInLastMonth, dailyMessageCounts) => ({
        user: req.user,
        messageCountByUser,
        userMessages,
        botMessages,
        messagesInLastWeek,
        messagesInLastMonth,
        dailyMessageCounts,
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
    page = adminPage // TODO
  } else if (path === '/') {
    page = statisticsPage // TODO
  }

  if (page) {
    Promise.join(
      buildInitialState(req),
      checksumPromise(bundleJsFilePath),
      checksumPromise(styleCssFilePath),
      (state, bundleJsChecksum, styleCssChecksum) => {
        const initialState = Object.assign(page.initialState, state)
        const checksums = {bundleJsChecksum, styleCssChecksum}
        res.send(ReactDOMServer.renderToString(basePage(page, initialState, checksums)))
      }
    ).catch(next)
  } else {
    next()
  }
}

app.get("/admin", auth.requireAdmin, renderApp)
app.get("/", renderApp)

const bundleJsFilePath = path.resolve(`${__dirname}/public/bundle.js`)
app.get('/bundle.js', serveStaticResource(bundleJsFilePath))
const styleCssFilePath = path.resolve(`${__dirname}/public/style.css`)
app.get('/style.css', serveStaticResource(styleCssFilePath))

app.listen(3000, () => {
  console.log('Listening on port 3000')
})
