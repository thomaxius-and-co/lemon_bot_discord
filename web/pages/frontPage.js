const React = require('react')

const pageTitle = 'Front Page'

const initialState = {}

const renderPage = () =>
  React.DOM.div(null,
    React.DOM.h1(null, 'Hello, world!'),
    React.DOM.p(null, 'This is the front page')
  )

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
