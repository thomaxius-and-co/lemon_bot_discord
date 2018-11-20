const React = require('react')
const {distinct, copy} = require('../util.js')
require('moment-timezone')
const {LineChart} = require('./chart')
const pageTitle = 'Faceit statistics'
const countryCodes = require ('../countryCodes.js')
const initialState = {
  faceit: -1
}


class Page extends React.Component {
  constructor(props) {
    super(props)
    this.state = props.state
  }
  render() {
    return(
      <div>
      <br/>{/*Todo: Hiero css:ää mieluummin*/}
        <h2>Personal stats for {this.state.playerDetails.nickname} <img src={this.state.playerDetails.avatar} height="52" width="52"/></h2>
        {faceitDetails(this.state.playerDetails)}
        {faceitStats(this.state.stats)}
        {faceitEloChart(this.state.personalWeeklyElo, this.state.rollingAverageElo)}
      </div>)
  }
}

const renderPage = state => <Page state={state} />

const faceitDetails = (apiPlayerDetails) => {
  const steamUrl = `https://steamcommunity.com/profiles/${apiPlayerDetails.steam_id_64}`
  const faceitUrl = apiPlayerDetails.faceit_url.replace('{lang}','en')
  return (
    <div>
    <p><a href={steamUrl}><img src={"https://orig00.deviantart.net/8fb4/f/2015/192/5/1/steam_logo_by_koolartist69-d90x4u8.png"} height="32" width="42"/></a> {/*I know this is dirty to link images and resize here, 
  but I'm not going to fight with making local images work today*/}
<a href={faceitUrl}><img src={"https://developers.faceit.com/static/media/logo.6c58ba31.svg"} height="32" width="32"/></a></p>
    <b>Membership type:</b> {apiPlayerDetails.membership_type}<br/>
    <b>Country:</b> {countryCodes[apiPlayerDetails.country.toUpperCase()]}<br/>
    {<b>Player bans:</b> && apiPlayerDetails.bans}
    </div>
  )
}

const faceitStats = (apiStats) => {

  const getSpecificPerMatchStat = (arg) => {
    let total = 0
    apiStats.segments.forEach((element) => total += parseInt(element.stats[arg]))
    let average = (total / (parseInt(apiStats.lifetime['Matches'].replace(',','').replace(' ','')))).toFixed(2) // kudos to the person who decided to put numbers as strings in the api
    return total + ` (${average} per match)`
  }

  const totalKrRatio = () => {
    let total = 0
    apiStats.segments.forEach((element) => total += parseInt(element.stats["K/R Ratio"]))
    return (total / (parseInt(apiStats.lifetime['Matches'].replace(',','').replace(' ','')))).toFixed(2) // kudos to the person who decided to put numbers as strings in the api
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
    let sorted = copy(segments)
      .filter(s => Number(s.stats["Wins"]) >= 10)
    if (sorted === undefined || sorted.length == 0) {
    return "-"
    }
    sorted.sort((a, b) => Number(a.stats["Win Rate %"]) - Number(b.stats["Win Rate %"]))
    .reverse()
    let mapWinPercentage = Number(sorted[0].stats["Win Rate %"])
    let mapNames = sorted.filter(_ => Number(_.stats["Win Rate %"]) === mapWinPercentage).map(_ => _.label)
    return mapWinPercentage + "% " + mapNames.join(', ')
  }


  return (
  <div>
  <b>Total matches</b>: {apiStats.lifetime['Matches']}<br/>
  <b>Total Wins</b>: {apiStats.lifetime['Wins']}<br/>
  <b>Win Rate</b>: {apiStats.lifetime['Win Rate %'] + '%'}<br/>
  <b>Best map winrate (over 10 matches played)</b>: {getBestMapWinPercentage(apiStats.segments)}<br/>
  <b>Average headshot percentage</b>: {apiStats.lifetime['Average Headshots %']} %<br/>
  <b>Average K/D Ratio</b>: {apiStats.lifetime['Average K/D Ratio']}<br/>
  <b>Average K/R Ratio</b>: {totalKrRatio()}<br/>
  <b>Average MVP's per match</b>: {getSpecificPerMatchStat('MVPs')}<br/> 
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
    xFormat: "%V/%Y",
  }
  const axis = {
    x: {
      label: "Week",
      type: "timeseries",
      tick: {format: "%V/%Y"}
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
     <h2>All time weekly elo history </h2>
      <LineChart data={data} axis={axis} grid={grid} line={{connectNull: true}} />
    </div>
  )
}



module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
