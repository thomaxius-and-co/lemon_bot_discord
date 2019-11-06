const React = require("react")
const ReactDOM = require("react-dom")

const basePage = require("./pages/basePage")
const statisticsPage = require("./pages/statisticsPage")
const gameStatisticsPage = require("./pages/gameStatisticsPage")
const faceitStatisticsPage = require("./pages/faceitStatisticsPage")
const personalFaceitStatsPage = require("./pages/personalFaceitStatsPage")
const whosaiditPage = require("./pages/whosaiditPage")
const adminPage = require("./pages/adminPage")
const Sentry = require("@sentry/browser")

const findPage = path => {
  switch (path) {
  case "/": return statisticsPage
  case "/admin": return adminPage
  case "/gamestatistics": return gameStatisticsPage  
  case "/faceitstatistics": return faceitStatisticsPage
  case "/personalfaceitstats": return personalFaceitStatsPage
  case "/whosaidit": return whosaiditPage
  case "/getquote": return whosaiditPage  
}
}
const currentPage = findPage(window.location.pathname)

class App extends React.Component {
  constructor(props) {
    super(props)
    const initialState = JSON.parse(document.getElementById("applicationState").getAttribute("data-state"))
    this.state = initialState
  }

  render() {
    return this.state
      ? basePage(currentPage, this.state, window.CHECKSUMS)
      : <span>Loading...</span>
  }
}

window.onload = () => {
  if (window.location.hostname !== "localhost") {
    Sentry.init({
      dsn: "https://d9974734991140ce9eb549909652a761@sentry.io/1809679",
      integrations: [
        new Sentry.Integrations.GlobalHandlers({
          onerror: true,
          onunhandledrejection: true,
        })
      ]
    })
  }

  ReactDOM.hydrate(<App/>, document)
}
