const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Faceit statistics'

const formatDate = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD')
const formatDateWithHHMM = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:MM')

function getDaysAgoString (date) {
  var daysAgo = subStractTime(date)
  if (daysAgo == 0) {
    return 'Today'
  }
  else if (daysAgo == 1) {
    return 'Yesterday'
  }
  else {
    return daysAgo + ' days ago'
  }
}

function subStractTime(date) {
  var today = new Date();
  var createdOn = new Date(date);
  var msInDay = 24 * 60 * 60 * 1000;
  
  createdOn.setHours(0,0,0,0);
  today.setHours(0,0,0,0)
  
  return Math.round((+today - +createdOn)/msInDay)
}

const initialState = {
  faceit: -1,
}

const withSign = n => {
  n = parseInt(n)
  if (n > 0) {
    return '+' + n
  } else if (n === null || n === 0 || !n) {
    return '-'
  } else {
    return String(n)
  }
}

let i = 1

const topFaceitTable = topFaceit =>
<table className="row">
<thead>
  <tr>
      <td>Rank</td>
      <td>Name</td>
      <td>EU ranking</td>
      <td>Elo</td>
      <td>Best elo</td>
      <td>Elo +- 30 days</td>
      <td>Elo +- 7 days</td>
      <td>Last seen</td> 
  </tr>
</thead>

<tbody>
  {topFaceit.map(x =>
    <tr key={x.epoch}>
      <td>#{i++}</td>
      <td>{x.name}</td>
      <td>{x.current_ranking}</td>
      <td>{x.current_elo}</td>
      <td>{x.best_score}</td>         
      <td>{withSign(x.difference_month)}</td>
      <td>{withSign(x.difference_week)}</td>
      <td>{getDaysAgoString(x.latest_entry)}</td>
    </tr>
  )}
</tbody>
</table>

const Faceit = ({faceit}) => {
 return <p>As of <b>{formatDateWithHHMM(faceit.latest_entry)} UTC</b></p>
}

const renderPage = state =>
  <div>
    <div className="row">
      <h1>Server toplist</h1> 
      {<Faceit faceit={state.latestFaceitEntry} />}
    </div>
    {topFaceitTable(state.topFaceit)}
    {thirtyDaysFaceitEloChart(state.eloForPast30Days)}
  </div>  


function getPlayerElementFromList(list, playername) {
  let playerElement = list.find(function(element) {
    if (element[0] == playername) {
      return element
    }
  });

  if (playerElement) {
    return playerElement
  }
  else {
    return false
  }
}

const thirtyDaysFaceitEloChart = (dailyEloMonth) => {

  var x = ["x"]
  var columns = [x]
  var groups = []

  dailyEloMonth.forEach(element => {
    let date = formatDate(element.day)
    if (x.indexOf(date) == -1) {
      x.push(date)
    }
    if (groups.indexOf(element.faceit_nickname == -1)) {
      groups.push(element.faceit_nickname)
    }
    let PlayerElement = getPlayerElementFromList(columns, element.faceit_nickname)
    if (PlayerElement) {
      let indexAtColumns = columns.indexOf(PlayerElement)
      columns[indexAtColumns].push(parseInt(element.elo))
    }
    else {
      columns.push(new Array(element.faceit_nickname, parseInt(element.elo)))
    }
  })


  const data = {
    x: "x",
    columns,
  types: {
  },
  groups: [],
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
      label: "Elo",
    },
  }
  const grid = {
    x: {
      lines: [
      ]
    }
  }
  return (
    <div>
      <h2>Elo developement for past 30 days</h2>
      <LineChart data={data} axis={axis} grid={grid} />
    </div>
  )
}



module.exports = {
  pageTitle,
  initialState,
  renderPage,
}