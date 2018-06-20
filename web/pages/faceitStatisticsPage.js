const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Faceit statistics'

const formatDate = date => moment(date).format('YYYY-MM-DD')
const formatDateWithHHMM = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:MM')

function relativeTime(date) {
  return moment(date).tz('UTC').fromNow()
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
  niskeFaceitDailyElo: [],
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
  {topFaceit.map((x, i) =>
    <tr key={x.name}>
      <td>#{i+1}</td>
      <td>{x.name}</td>
      <td>{x.current_ranking}</td>
      <td>{x.current_elo}</td>
      <td>{x.best_score}</td>         
      <td>{withSign(x.difference_month)}</td>
      <td>{withSign(x.difference_week)}</td>
      <td>{relativeTime(x.latest_entry)}</td>
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

function countOccurence(array) {
  let count = 0
  array.forEach(element => {
    let thecount = countOccurenceHelperFunction(array, element.faceit_nickname)
    if (thecount > count) {
      count = thecount
    }
  })
  return count
}

function countOccurenceHelperFunction(array, faceit_nickname) {
  let count = 0
  array.forEach(element => {
    if (element.faceit_nickname == faceit_nickname) {
      count++
    }
  })
  return count
}



const thirtyDaysFaceitEloChart = (dailyEloMonth) => {
  count = countOccurence(dailyEloMonth) //Count how many days that contain elo updates are in the database
  let x = ["x"]
  let columns = [x]
  let groups = []

  // Add each playername that has elo updates into columns array, and set a null value for each elo per day
  dailyEloMonth.forEach(element => {groups.indexOf(element.faceit_nickname) == -1 && groups.push(element.faceit_nickname)}) 
  groups.forEach(faceit_nickname => {
    let playerArrayElement = new Array()
    playerArrayElement.push(faceit_nickname)
    for (i=0;count>=i;i++) {
      playerArrayElement.push(null)
    }
    columns.push(playerArrayElement)
  })
  
  dailyEloMonth.forEach(element => { // add dates into dates array

    let date = formatDate(element.day)

    if (x.indexOf(date) == -1) {
      x.push(date)
    }

    let playerElement = columns.find(subElement => subElement[0] == element.faceit_nickname) // get existing players element
    if (playerElement) {
      let indexOfPlayerElementAtColumns = columns.indexOf(playerElement)
      playerElement[x.indexOf(date)] = parseInt(element.elo)
      columns[indexOfPlayerElementAtColumns] = playerElement
    }
  })
  columns.forEach(element => { // Because not every player plays every day, we need to store their elo value from previous day as their elo value for the day they haven't played
  for (i=2;element.length>i;i++) {
      if (element[i] == null && element[i-1] != null) {
        element[i] = element[i-1]
      }
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
     <h2>Average elo for the past 30 days</h2>
      <LineChart data={data} axis={axis} grid={grid} line={{connectNull: true}} />
    </div>
  )
}



module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
