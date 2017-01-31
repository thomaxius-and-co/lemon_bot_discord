const React = require('react')

const pageTitle = 'Front Page'

const initialState = {
  totalMessages: -1,
  messagesInLast7Days: -1,
}

const renderPage = state =>
  <div>
    <h1>Discord statistics</h1>
    <p>Total messages {state.totalMessages}</p>
    <p>Messages in last 7 days {state.messagesInLast7Days}</p>
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
