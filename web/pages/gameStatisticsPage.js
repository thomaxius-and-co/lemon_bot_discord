const React = require('react')
const moment = require('moment')
require('moment-timezone')
const {LineChart} = require('./chart')

const pageTitle = 'Game statistics'

const initialState = {
  userMessages: -1,
  botMessages: -1,
  messagesInLastWeek: -1,
  messagesInLastMonth: -1,
  spammer: -1,
  topSlots: [],
  topBlackjack: [],
  topWhosaidit: [],
  whosaiditWeeklyWinners: [],
}

const formatDate = epochMs => moment(epochMs).tz('UTC').format('YYYY-MM-DD')
const formatNum = (n, decimals) => n.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, " ")

const topSlotsTable = topSlots =>
  <table className="row">
    <thead>
      <tr>
          <td>Rank</td>
          <td>Name</td>
          <td>Total games played</td>
          <td>Wins</td>
          <td>Losses</td>
		  <td>Profit</td>
		  <td>Win %</td>
		  <td>Money spent</td>
      </tr>
    </thead>
    <tbody>
      {topSlots.map(x =>
        <tr key={x.epoch}>
          <td>{x.rank}</td>
          <td>{x.name}</td>
          <td>{x.total}</td>
          <td>{x.wins_slots}</td>
          <td>{x.losses_slots}</td>
		  <td>{x.profit}$</td>
		  <td>{formatNum(Number(x.percentage),2)}%</td>
		  <td>{x.moneyspent_slots}$</td>
        </tr>
      )}
    </tbody>
  </table>

const topBlackjackTable = topBlackjack =>
  <table className="row">
    <thead>
      <tr>
          <td>Rank</td>
          <td>Name</td>
		  <td>Games played</td>
		  <td>Wins</td>
		  <td>Losses</td>
          <td>Surrenders</td>
		  <td>Ties</td>
		  <td>Win %</td>
          <td>Money spent</td>
		  <td>Money won</td>
      </tr>
    </thead>
    <tbody>
      {topBlackjack.map(x =>
        <tr key={x.epoch}>
          <td>{x.rank}</td>
          <td>{x.name}</td>
		  <td>{formatNum(Number(x.total_games), 0)}</td>
          <td>{x.wins_bj}</td>
          <td>{x.losses_bj}</td>
          <td>{x.surrenders}</td>
		  <td>{x.ties}</td>
		  <td>{formatNum(Number(x.winpercentage),2)}%</td>
		  <td>{x.moneyspent_bj}$</td>
		  <td>{x.moneywon_bj}$</td>
        </tr>
      )}
    </tbody>
  </table>

const whosaiditWeeklyWinnersTable = whosaiditWeeklyWinners =>
  <table className="row">
    <thead>
      <tr>
          <td>Name</td>
		  <td>Dateadded</td>
          <td>Score</td>
          <td>Wins</td>
		  <td>Losses</td>
      </tr>
    </thead>
    <tbody>
      {whosaiditWeeklyWinners.map(x =>
        <tr key={x.epoch}>
          <td>{x.name}</td>
		  <td>{String(formatDate(x.dateadded))}</td>
		  <td>{formatNum(Number(x.score),2)}</td>
          <td>{x.wins}</td>
          <td>{x.losses}</td>
        </tr>
      )}
    </tbody>
  </table>    
  
const topWhosaiditTable = topWhosaidit =>
  <table className="row">
    <thead>
      <tr>
	      <td>Rank</td>
          <td>Name</td>
		  <td>Total games</td>
          <td>Correct</td>
		  <td>Percentage</td>
		  <td>Bonus percentage</td>
      </tr>
    </thead>
    <tbody>
      {topWhosaidit.map(x =>
        <tr key={x.epoch}>
          <td>{x.rank}</td>
		  <td>{x.name}</td>
          <td>{x.total}</td>
		  <td>{x.wins}</td>
          <td>{formatNum(Number(x.ratio), 2)}</td>
		  <td>{formatNum(Number(x.bonuspct), 2)}</td>
        </tr>
      )}
    </tbody>
  </table>  
  
const renderPage = state => {
  return <div>
    <div className="row">
      <h1>Top slots</h1>
    </div>
    {topSlotsTable(state.topSlots)}
    <div className="row">
      <h1>Top blackjack</h1>
	  <p><i>Top 10 blackjack players.)</i></p>
    </div>
    {topBlackjackTable(state.topBlackjack)}
    <div className="row">
      <h1>Top Whosaidit</h1>
	  <p><i>Top 10 whosaidit players. A game where one has to guess who is the author of a given quote. This table is reseted weekly.</i></p>
    </div>
    {topWhosaiditTable(state.topWhosaidit)}	
    <div className="row">
      <h1>Whosaidit weekly winners</h1>
	  <p><i>Weekly winners of whosaidit</i></p>
    </div>
    {whosaiditWeeklyWinnersTable(state.whosaiditWeeklyWinners)}	
  </div>  
}

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
