const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Faceit statistics'

const initialState = {

}

const withSign = n => {
  if (n > 0) {
    return '+' + n
  } else if (n === null) {
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
      <td>Ranking</td>
      <td>Elo</td>
      <td>Elo change 30 days</td>
  </tr>
</thead>
<tbody>
  {topFaceit.map(x =>
    <tr key={x.epoch}>
      <td>{x.rank}</td>
      <td>{x.name}</td>
      <td>{x.current_ranking}</td>
      <td>{x.current_elo}</td>
      <td>{withSign(x.difference)}</td>
    </tr>
  )}
</tbody>
</table>

const renderPage = state => {
  return <div>
    <div className="row">
      <h1>Server faceit toplist</h1>
    </div>
    {topFaceitTable(state.topFaceit)}
  </div>  
}

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
