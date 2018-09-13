const React = require('react')
const moment = require('moment')
const {distinct} = require('../util.js')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Faceit statistics'

const formatDateWithHHMM = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:MM')

const median = (numbers) => {
  numbers.sort()
  return numbers.length % 2 === 0 ? ((numbers[numbers.length / 2 - 1] + numbers[numbers.length / 2]) / 2) : numbers[(numbers.length - 1) / 2]
  }

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
        {thirtyDaysFaceitEloChart(this.state.personalWeeklyElo, this.state.personalEloWeeklyMedian)}
      </div>)
  }
}

const renderPage = state => <Page state={state} />

const thirtyDaysFaceitEloChart = (weeklyElo, weeklyMedian) => {
  const weeks = distinct(weeklyElo.map(x => x.week))
  const nickname = distinct(weeklyElo.map(x => x.faceit_nickname))

  const playersColumns = nickname.map(nickname => {
    const findRowForDate = week => weeklyElo.find(row => row.faceit_nickname === nickname && row.week === week)
    const optElo = row => row ? Number(row.elo) : null
    const points = weeks.map(findRowForDate).map(optElo)
    return ["Weekly elo", ...points]
  })

  function getPlayersMedianColumns() { //TODO: Make this horrification properly
    let tempArr = []
    let medianArr = []
    let currentWeek = ''
    weeklyMedian.forEach((element) => {
      !currentWeek && (currentWeek = element.week)
      element.week == currentWeek && tempArr.push(Number(element.elo))
      if ((element.week != currentWeek) || (element == weeklyMedian[weeklyMedian.length -1])) {
        medianArr.push(median(tempArr))
        tempArr = []
        currentWeek = element.week
      }

    })
    return [["Median", ...medianArr]]
  }

  const columns = [
    ["x", ...weeks],
    ...playersColumns, ...getPlayersMedianColumns()
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
