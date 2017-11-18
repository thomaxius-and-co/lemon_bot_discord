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
      <h1>Global statistics</h1>
      <p>Total messages: <b>{formatNum(state.userMessages + state.botMessages)}</b></p>
      <p><i>({formatNum(state.userMessages)} by users, {formatNum(state.botMessages)} by bots)</i></p>
      <p>Messages in last week: <b>{formatNum(state.messagesInLastWeek)}</b> </p>
      <p>Messages in last month: <b>{formatNum(state.messagesInLastMonth)}</b> </p>
	  {state.spammer && <Spammer spammer={state.spammer} />}
    </div>
    {dailyMessageCountChart(state.dailyMessageCounts, state.rolling7DayMessageCounts)}
    {weekdayCountChart(state.messagesPerWeekday7, state.messagesPerWeekday30, state.messagesPerWeekday90, state.messagesPerWeekday360)}
  </div>

const dailyMessageCountChart = (dailyMessageCounts, rolling7DayMessageCounts) => {
  const averages = rolling7DayMessageCounts.map(_ => Math.round(_.average))

  const data = {
    x: "x",
    columns: [
      ["x"].concat(dailyMessageCounts.map(_ => formatDate(_.epoch))),
      ["Users"].concat(dailyMessageCounts.map(_ => _.user_count)),
      ["Bots"].concat(dailyMessageCounts.map(_ => _.bot_count)),
      ["Rolling 7 day average"].concat(averages),
    ],
    types: {
      "Users": "area-spline",
      "Bots": "area-spline",
      "Rolling 7 day average": "spline",
    },
    groups: [["Users", "Bots"]],
  }
  const axis = {
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
  const grid = {
    x: {
      lines: [
        { value: moment("2017-11-03T17:00:00+02:00").valueOf(), text: "Harry Spa v4.0 START" },
        { value: moment("2017-11-05T10:00:00+02:00").valueOf(), text: "Harry Spa v4.0 END" },
        { value: moment("2017-11-17T16:00:00+02:00").valueOf(), text: "HelmiLAN START" },
        { value: moment("2017-11-19T12:00:00+02:00").valueOf(), text: "HelmiLAN END" },
      ]
    }
  }

  return (
    <div>
      <h2>Messages per per day in the last month</h2>
      <LineChart data={data} axis={axis} grid={grid} />
    </div>
  )
}

const weekdayCountChart = (counts7, counts30, counts90, counts360) => {
  const mkColumn = (title, counts) => [title].concat(counts.map(_ => Math.round(_.messages)))
  const data = {
    x: "Weekday",
    columns: [
      ["Weekday", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"],
      mkColumn("week", counts7),
      mkColumn("month", counts30),
      mkColumn("3 months", counts90),
      mkColumn("year", counts360),
    ],
    types: {
      "week": "spline",
      "month": "spline",
      "3 months": "spline",
      "year": "spline",
    },
  }
  const axis = {
    x: {
      label: "Weekday",
      type: "category",
    },
    y: {
      label: "Average messages",
    },
  }
  return (
    <div>
      <h2>Messages per weekday on average</h2>
      <LineChart data={data} axis={axis} />
    </div>
  )
}

const OK_HAND = String.fromCodePoint(0x1F44C)
const DISSAPOINTED = String.fromCodePoint(0x1F61E)

const Profile = ({user}) => {
  const {id, username, discriminator, avatar, mfa_enabled} = user
  const avatarUrl = `https://cdn.discordapp.com/avatars/${id}/${avatar}.webp?size=256`
  const mfa = mfa_enabled
    ? <div>MFA enabled {OK_HAND}</div>
    : <div>MFA not enabled {DISSAPOINTED}</div>
  return (
    <div className="profile">
      <img className="profile-avatar" src={avatarUrl} />
      <div className="profile-info">
        <div className="profile-username" >{username}<span className="profile-discriminator">#{discriminator}</span></div>
        {mfa}
      </div>
    </div>
  )
}

const UserStats = ({user, messageCount}) =>
  <div>
    <h1>Personal stats</h1>
    <Profile user={user} />
    <p>You, {user.username}#{user.discriminator}, have written {formatNum(messageCount)} messages.</p>
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
