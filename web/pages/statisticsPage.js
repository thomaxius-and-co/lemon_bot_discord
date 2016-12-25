const React = require('react')

const pageTitle = 'Front Page'

const initialState = {
  totalMessages: -1,
}

const renderPage = state =>
  React.DOM.div(null,
    React.DOM.h1(null, 'Discord bot statistics'),
    React.DOM.p(null, `Total messages ${state.totalMessages}`)
  )

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
