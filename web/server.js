const crypto = require('crypto')
const path = require('path')
const express = require('express')
const React = require('react')
const ReactDOM = require('react-dom')
const ReactDOMServer = require('react-dom/server')

const basePage = require('./pages/basePage')
const frontPage = require('./pages/frontPage')

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
      res.setHeader('Cache-Control', `public, max-age=${oneYearInSeconds}`)
      res.sendFile(filePath)
    } else {
      res.status(404).end()
    }
  })
  .catch(next)
}

const app = express()

app.get('*', (req, res, next) => {
  console.log(`Requested ${req.originalUrl}`)
  const path = req.originalUrl
  if (path === '/') {
    const page = frontPage // TODO
    checksumPromise(bundleJsFilePath).then(bundleJsChecksum => {
      res.send(ReactDOMServer.renderToString(basePage(page, page.initialState, { bundleJsChecksum })))
    })
  } else {
    next()
  }
})

const bundleJsFilePath = path.resolve(`${__dirname}/.generated/bundle.js`)
app.get('/bundle.js', serveStaticResource(bundleJsFilePath))

app.listen(3000, () => {
  console.log('Listening on port 3000')
})
