const React = require('react')

const pageTitle = 'Front Page'

const initialState = {
  totalMessages: -1,
  messagesInLastWeek: -1,
  messagesInLastMonth: -1,
}

const renderPage = state =>
  <div>
    <h1>Discord statistics</h1>
    <p>Total messages {state.totalMessages}</p>
    <p>Messages in last week {state.messagesInLastWeek}</p>
    <p>Messages in last month {state.messagesInLastMonth}</p>
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
