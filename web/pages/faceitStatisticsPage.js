const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Faceit statistics'

const formatDate = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD HH:mm')

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
    </tr>
  )}
</tbody>
</table>

const Faceit = ({faceit}) => {
 return <p>As of <b>{formatDate(faceit.latest_entry)} UTC</b></p>
}

const renderPage = state => {
  return <div>
    <div className="row">
      <h1>Server toplist</h1> 
      {<Faceit faceit={state.latestFaceitEntry} />}
    </div>
    {topFaceitTable(state.topFaceit)}
  </div>  
}

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}