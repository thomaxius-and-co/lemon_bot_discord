const React = require('react')
const moment = require('moment')
const {distinct} = require('../util.js')
require('moment-timezone')
const {LineChart} = require('./chart')
const pageTitle = 'Faceit statistics'

const formatDateWithHHMM = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:MM')

const initialState = {
  faceit: -1
}

const LastUpdateTime = ({faceit}) => {
  return <p>As of <b>{formatDateWithHHMM(faceit.latest_entry)} UTC</b></p>
}

class Page extends React.Component {
  constructor(props) {
    super(props)
    this.state = props.state
  }
  render() {
    return(
      <div>
        {<LastUpdateTime faceit={this.state.latestFaceitEntry} />}
        {faceitStats(this.state.stats)}
        {faceitEloChart(this.state.personalWeeklyElo, this.state.rollingAverageElo)}
      </div>)
  }
}

const renderPage = state => <Page state={state} />

const faceitStats = (apiStats) => {
  return (
  <div>
  Average headshot percentage: {apiStats.lifetime['Average Headshots %']} %<br/>
  Average K/D Ratio: {apiStats.lifetime['Average K/D Ratio']}<br/>
  Current Win Streak: {apiStats.lifetime['Current Win Streak']}<br/>
  K/D Ratio: {parseFloat(apiStats.lifetime['K/D Ratio'].replace(',','.').replace(' ','')).toFixed(2)}<br/>
  Longest Win Streak: {apiStats.lifetime['Longest Win Streak']}<br/>
  Total matches: {apiStats.lifetime['Matches']}<br/>
  Last five matches: {apiStats.lifetime['Recent Results'].map((element) => (element == 0) ? <font color="red">L </font> : <font color="green ">W </font>)}<br/>
  Total Headshot %: {parseFloat(apiStats.lifetime['Total Headshots %'].replace(',','.').replace(' ','')).toFixed(2)}<br/>
  Win Rate %: {apiStats.lifetime['Win Rate %']}<br/>
  Total Wins: {apiStats.lifetime['Wins']}<br/>
  <br/>
  </div>
)
}

const faceitEloChart = (weeklyElo, rollingAverage) => {
  const weeks = distinct(weeklyElo.map(x => x.week))
  const nickname = distinct(weeklyElo.map(x => x.faceit_nickname))

  const playersColumns = nickname.map(nickname => {
    const findRowForDate = week => weeklyElo.find(row => row.faceit_nickname === nickname && row.week === week)
    const optElo = row => row ? Number(row.elo) : null
    const points = weeks.map(findRowForDate).map(optElo)
    return ["Weekly elo", ...points]
  })

  const playersrollingAverageColumns = nickname.map(nickname => {
    const findRowForDate = week => rollingAverage.find(row => row.faceit_nickname === nickname && row.week === week)
    const optElo = row => row ? Number(row.average) : null
    const points = weeks.map(findRowForDate).map(optElo)
    return ["Rolling 4 week average", ...points]
  })

  const columns = [
    ["x", ...weeks],
    ...playersColumns, ...playersrollingAverageColumns
  ]
  const data = {
    x: "x",
    columns,
    xFormat: "%W/%Y",
  }
  const axis = {
    x: {
      label: "Week",
      type: "timeseries",
      tick: {format: "%W/%Y"}
    },
    y: {
      label: "Elo",
    },
  }
  const grid = {
    y: {
      lines: [
        { value: 0, text: "Level 1" },
        { value: 801, text: "Level 2" },
        { value: 951, text: "Level 3" },
        { value: 1101, text: "Level 4" },
        { value: 1251, text: "Level 5" },
        { value: 1401, text: "Level 6" },
        { value: 1551, text: "Level 7" },
        { value: 1701, text: "Level 8" },
        { value: 1851, text: "Level 9" },
        { value: 2001, text: "Level 10" },
      ]
    }
  }

  return (
    <div>
     <h2>All time weekly elo history for {nickname}</h2>
      <LineChart data={data} axis={axis} grid={grid} line={{connectNull: true}} />
    </div>
  )
}



module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
