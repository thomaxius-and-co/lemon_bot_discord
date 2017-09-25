const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Discord statistics'

const initialState = {
  userMessages: -1,
  botMessages: -1,
  messagesInLastWeek: -1,
  messagesInLastMonth: -1,
  spammer: -1,
  dailyMessageCounts: [],
}

const formatDate = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD')

const formatNum = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ")

const dailyMessageCountTable = dailyMessageCounts =>
  <table className="row">
    <thead>
      <tr>
          <td>Date</td>
          <td>User messages</td>
          <td>Bot messages</td>
      </tr>
    </thead>
    <tbody>
      {dailyMessageCounts.map(x =>
        <tr key={x.epoch}>
          <td>{formatDate(x.epoch)}</td>
          <td>{formatNum(x.user_count)}</td>
          <td>{formatNum(x.bot_count)}</td>
        </tr>
      )}
    </tbody>
  </table>

const Spammer = props =>
  <div>{props.spammer}</div>

const render = state =>
  <div>
    {state.spammer && <Spammer spammer={state.spammer} />}
  </div>
  
const renderPage = state =>
  <div>
    <div className="row">
      {state.user && <UserStats user={state.user} messageCount={state.messageCountByUser}/>}
      <h1>Discord statistics</h1>
      <p>Total messages: <b>{formatNum(state.userMessages + state.botMessages)}</b></p>
      <p><i>({formatNum(state.userMessages)} by users, {formatNum(state.botMessages)} by bots)</i></p>
      <p>Messages in last week: <b>{formatNum(state.messagesInLastWeek)}</b> </p>
      <p>Messages in last month: <b>{formatNum(state.messagesInLastMonth)}</b> </p>
	  <p>Spammer of the day: <b>{state.spammer.spammeroftheday}</b> with {state.spammer.message_count} messages.</p>
    </div>
    {dailyMessageCountChart(state.dailyMessageCounts)}
    {dailyMessageCountTable(state.dailyMessageCounts)}
  </div>

const mangleCountsIntoChartFormat = counts => {
  return {
    data: {
      x: "x",
      columns: [
        ["x"].concat(counts.map(_ => formatDate(_.epoch))),
        ["user_count"].concat(counts.map(_ => _.user_count)),
        ["bot_count"].concat(counts.map(_ => _.bot_count)),
      ],
      types: {
        user_count: "area-spline",
        bot_count: "area-spline",
      },
      groups: [["user_count", "bot_count"]],
    },
    axis: {
      x: {
        type: "timeseries",
        tick: {
          format: "%Y-%m-%d"
        }
      }
    }
  }
}
const dailyMessageCountChart = dailyMessageCounts => {
  const {data, axis} = mangleCountsIntoChartFormat(dailyMessageCounts)
  return <LineChart data={data} axis={axis} />
}

const UserStats = props =>
  <div>
    <h1>Personal stats</h1>
    <p>You, {props.user.username}#{props.user.discriminator}, have written {formatNum(props.messageCount)} messages.</p>
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
