const React = require('react')
const ReactDOM = require('react-dom')

const basePage = require('./pages/basePage')
const statisticsPage = require('./pages/statisticsPage')
const gameStatisticsPage = require('./pages/gameStatisticsPage')
const faceitStatisticsPage = require('./pages/faceitStatisticsPage')
const adminPage = require('./pages/adminPage')

const findPage = path => {
  switch (path) {
  case "/": return statisticsPage
  case "/admin": return adminPage
  case "/gameStatisticsPage": return gameStatisticsPage  
  case "/faceitStatisticsPage": return faceitStatisticsPage    
}
}
const currentPage = findPage(window.location.pathname)

class App extends React.Component {
  constructor(props) {
    super(props)
    const initialState = JSON.parse(document.getElementById('applicationState').getAttribute('data-state'))
    this.state = initialState
  }

  render() {
    return this.state
      ? basePage(currentPage, this.state, window.CHECKSUMS)
      : <span>Loading...</span>
  }
}

window.onload = () => ReactDOM.hydrate(<App/>, document)
