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
    for (i=1;count>=i;i++) {
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

 console.log(data)

  columns.forEach(element => { // Because not every player plays every day, we need to store their elo value from previous day as their elo value for the day they haven't played
    element.forEach(subElement => {
      if (typeof subElement != 'string' && (typeof element[element.indexOf(subElement)-1] != 'string' && element[element.indexOf(subElement)-1] != null) && subElement == null) {
        element[element.indexOf(subElement)] = element[element.indexOf(subElement)-1]
      }
      else if (element[element.length-1] == null) {
        element[element.length-1] = element[element.length-2]
      }
    
      })})
    
  console.log(data)

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