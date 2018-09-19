const React = require('react')
const moment = require('moment')
const {distinct, copy} = require('../util.js')
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

  const getSpecificPerMatchStat = (arg) => {
    let total = 0
    apiStats.segments.forEach((element) => total += parseInt(element.stats[arg]))
    let average = (total / (parseInt(apiStats.lifetime['Matches'].replace(',','').replace(' ','')))).toFixed(2) // kudos to the person who decided to put numbers as strings in the api
    return total + ` (${average} per match)`
  }


  const getSpecificPerRoundStat = (arg) => {
    let total = 0
    let totalRounds = 0
    apiStats.segments.forEach((element) => {
      total += parseInt(element.stats[arg].replace(',',''))  // kudos to the person who decided to put numbers as strings in the api
      totalRounds += parseInt(element.stats['Rounds'].replace(',','')) 
    })
    let average = (total / totalRounds).toFixed(2)
    return total + ` (${average} per round)`
  }

  const getBestMapWinPercentage = segments => {
    const sorted = copy(segments)
      .filter(s => Number(s.stats["Wins"]) >= 10)
      .sort((a, b) => Number(a.stats["Win Rate %"]) - Number(b.stats["Win Rate %"]))
      .reverse()
    let mapWinPercentage = Number(sorted[0].stats["Win Rate %"])
    let mapNames = sorted.filter(_ => Number(_.stats["Win Rate %"]) === mapWinPercentage).map(_ => _.label)
    console.log(mapNames)
    return mapWinPercentage + "% " + mapNames.join(', ')
  }


  return (
  <div>
  <p>Note: Due to a bug in the Faceit api, some of the stats on this page are currently inaccurate.</p>
  <b>Total matches</b>: {apiStats.lifetime['Matches']}<br/>
  <b>Total Wins</b>: {apiStats.lifetime['Wins']}<br/>
  <b>Win Rate</b>: {apiStats.lifetime['Win Rate %'] + '%'}<br/>
  <b>Best map winrate</b>: {getBestMapWinPercentage(apiStats.segments)}<br/>
  <b>Average headshot percentage</b>: {apiStats.lifetime['Average Headshots %']} %<br/>
  <b>Average K/D Ratio</b>: {apiStats.lifetime['Average K/D Ratio']}<br/>
  <b>Total MVP's</b>: {getSpecificPerRoundStat("MVPs")}<br/>
  <b>Total kills</b>: {getSpecificPerRoundStat("Kills")}<br/> 
  <b>Total deaths</b>: {getSpecificPerRoundStat("Deaths")}<br/> 
  <b>Current Win Streak</b>: {apiStats.lifetime['Current Win Streak']}<br/>
  <b>Longest Win Streak</b>: {apiStats.lifetime['Longest Win Streak']}<br/>
  <b>Total Penta kills</b>: {getSpecificPerMatchStat("Penta Kills")}<br/>
  <b>Total Quadro Kills</b>: {getSpecificPerMatchStat("Quadro Kills")}<br/>
  <b>Total Triple Kills</b>: {getSpecificPerMatchStat("Triple Kills")}<br/>
  <b>Last five matches</b>: {apiStats.lifetime['Recent Results'].map((element) => (element == 0) ? <font color="red">L </font> : <font color="green ">W </font>)}<br/>
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
