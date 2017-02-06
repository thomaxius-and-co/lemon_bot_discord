const React = require('react')

const pageTitle = 'Discord statistics'

const initialState = {
  totalMessages: -1,
  messagesInLastWeek: -1,
  messagesInLastMonth: -1,
  dailyMessageCounts: [],
}

const dateFormat = new Intl.DateTimeFormat('fi', {
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
})

const formatDate = date => dateFormat.format(date)

const dailyMessageCountTable = dailyMessageCounts =>
  <table>
    <thead>
      <tr>
          <td>Date</td>
          <td>Messages</td>
      </tr>
    </thead>
    <tbody>
      {dailyMessageCounts.map(x =>
        <tr key={x.epoch}>
          <td>{formatDate(new Date(x.epoch))}</td>
          <td>{x.count}</td>
        </tr>
      )}
    </tbody>
  </table>

const renderPage = state =>
  <div>
    <h1>Discord statistics</h1>
    <p>Total messages {state.totalMessages}</p>
    <p>Messages in last week {state.messagesInLastWeek}</p>
    <p>Messages in last month {state.messagesInLastMonth}</p>
    {dailyMessageCountTable(state.dailyMessageCounts)}
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
