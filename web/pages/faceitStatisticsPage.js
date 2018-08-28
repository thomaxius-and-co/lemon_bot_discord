const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')
const {distinct} = require('../util.js')

const pageTitle = 'Faceit statistics'

const formatDateWithHHMM = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:MM')

function relativeTime(date) {
  return moment(date).tz('UTC').fromNow()
}

const initialState = {
  faceit: -1
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

class TopFaceitTable extends React.Component {
  constructor(props) {
    super(props)
    this.state = props.state
    this.sortTable = this.sortTable.bind(this)
    this.state = {
      lastSorted: ''
    }
  }
    
  sortTable(sortby) {
    let topFaceit = this.props.topFaceit
    topFaceit.sort(
      function(a, b) 
        {
          if (!isNaN(parseInt(a[sortby])) && !isNaN(parseInt(b[sortby]))) {
            return parseInt(a[sortby]) - parseInt(b[sortby])
          }
          if (typeof a[sortby] === 'string' || a[sortby] instanceof String) {
            let x = a[sortby].toLowerCase();
            let y = b[sortby].toLowerCase();
              if (x < y) {
                return -1
              }
              if (x > y) {
                return 1
              }
              return 0
            }
            else {
              return
            }
        }
      )
    let lastSorted = sortby
    if (lastSorted == this.state.lastSorted) {
      topFaceit.reverse()
      lastSorted = ''
    }

    this.setState(() => {
      return {
        topFaceit: topFaceit,
        lastSorted: lastSorted
      }
    })
    
  }
  render() {

    const topFaceit = this.props.topFaceit    
        return(
    <table className="row">
    <thead>
      <tr>
          <td>Rank</td>
          <td onClick={() => this.sortTable("name")}>Name</td>
          <td onClick={() => this.sortTable("current_ranking")}>EU ranking</td>
          <td onClick={() => this.sortTable("current_elo")}>Elo</td>
          <td onClick={() => this.sortTable("best_score")}>Best elo</td>
          <td onClick={() => this.sortTable("difference_month")}>Elo +- 30 days</td>
          <td onClick={() => this.sortTable("difference_week")}>Elo +- 7 days</td>
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
    )
  }
}

const Faceit = ({faceit}) => {
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
        <div className="row">
          <h1>Server toplist</h1> 
          {<Faceit faceit={this.state.latestFaceitEntry} />}
        </div>
        <TopFaceitTable topFaceitTable topFaceit={this.state.topFaceit}/>
        {thirtyDaysFaceitEloChart(this.state.eloForPast30Days)}
      </div>)
  }
}

const renderPage = state => <Page state={state} />

const thirtyDaysFaceitEloChart = (dailyEloMonth) => {
  const days = distinct(dailyEloMonth.map(x => x.day))
  const nicknames = distinct(dailyEloMonth.map(x => x.faceit_nickname))

  const playerColumns = nicknames.map(nickname => {
    const findRowForDate = day => dailyEloMonth.find(row => row.faceit_nickname === nickname && row.day === day)
    const optElo = row => row ? Number(row.elo) : null
    const points = days.map(findRowForDate).map(optElo)
    return [nickname, ...points]
  })

  const columns = [
    ["x", ...days],
    ...playerColumns,
  ]

  const data = {
    x: "x",
    columns,
    xFormat: "%Y-%m-%dT%H:%M:%S.%L%Z",
  }
  const axis = {
    x: {
      label: "Date",
      type: "timeseries",
      tick: {format: "%Y-%m-%d"}
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
