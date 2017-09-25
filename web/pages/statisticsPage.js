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

const Spammer = props =>
  <p>Spammer of the day: <b>{props.spammer.spammeroftheday}</b> with {props.spammer.message_count} messages.</p>
  
const renderPage = state =>
  <div>
    <div className="row">
      {state.user && <UserStats user={state.user} messageCount={state.messageCountByUser}/>}
      <h1>Discord statistics</h1>
      <p>Total messages: <b>{formatNum(state.userMessages + state.botMessages)}</b></p>
      <p><i>({formatNum(state.userMessages)} by users, {formatNum(state.botMessages)} by bots)</i></p>
      <p>Messages in last week: <b>{formatNum(state.messagesInLastWeek)}</b> </p>
      <p>Messages in last month: <b>{formatNum(state.messagesInLastMonth)}</b> </p>
	  {state.spammer && <Spammer spammer={state.spammer} />}
    </div>
    {dailyMessageCountChart(state.dailyMessageCounts)}
  </div>

const mangleCountsIntoChartFormat = counts => {
  return {
    data: {
      x: "x",
      columns: [
        ["x"].concat(counts.map(_ => formatDate(_.epoch))),
        ["Users"].concat(counts.map(_ => _.user_count)),
        ["Bots"].concat(counts.map(_ => _.bot_count)),
      ],
      types: {
        user_count: "area-spline",
        bot_count: "area-spline",
      },
      groups: [["Users", "Bots"]],
    },
    axis: {
      x: {
        label: "Date",
        type: "timeseries",
        tick: {
          format: "%Y-%m-%d"
        }
      },
      y: {
        label: "Messages",
      },
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
