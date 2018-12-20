const React = require("react")
const moment = require("moment-timezone")
const axios = require("axios")
const pageTitle = "Faceit statistics"
const initialState = {
  playing: false,
  availableWhoSaiditUsers: null,
  quote: null,
  error: null,
  correct: "",
  user: {},
  response: null,
  counterEnabled: false,
  seconds: 10
}

const renderPage = state => <Page state={state} />
const formatNum = (n, decimals) => n.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, " ")

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
          <td className="rank">{x.rank}</td>
		  <td>{x.name}</td>
          <td>{x.total}</td>
		  <td>{x.wins}</td>
          <td>{formatNum(Number(x.ratio), 2)}</td>
		  <td>{formatNum(Number(x.bonuspct), 2)}</td>
        </tr>
      )}
    </tbody>
  </table>


class Page extends React.Component {
  constructor(props) {
    super(props)
    this.state = props.state
    this.startGame = this.startGame.bind(this)
    this.setPlaying = this.setPlaying.bind(this)
    this.setDisabled = this.setDisabled.bind(this)
  }

  startGame() {
    this.setState({loading: true})
    axios.post("/whosaidit").then(response => {
      this.setState({
        loading: false,
        playing: true,
        quote: response.data.quote,
        error: response.data.error,
        availableWhoSaiditUsers: response.data.availableWhoSaiditUsers,
        disabled: false,
      })
    })
  }

  setPlaying(boolean) {
     this.setState({playing:boolean})
  }

  setDisabled(boolean) {
    this.setState({disabled:boolean})
 }

  updateTable() {
    axios.post("/getTable").then((result) => {
      this.setState({topWhosaidit:result.data.table})
    })
  }

  render() {
    return(
      <div>
      <br/>
      <br/>
      <br/>
      <h1>Welcome to Whosaidit!</h1>
      <br/>
      <br/>
      <br/>
      <div className="row">
        <h2>Current leaderboard</h2>
        <i>Press refresh to refresh the table</i>
      </div>
      {<input type="button" clasName="whosaiditChoiceButtonBlue" value="Refresh" onClick={()=> this.updateTable()} />}
      {topWhosaiditTable(this.state.topWhosaidit)}	
      {<input type="button" disabled={(this.state.playing || this.state.disabled || this.state.loading) && "true"} id="gameStartButton" value="New game" className="whosaiditChoiceButtonBlue" onClick={this.startGame}></input>}
      {this.state.loading && <div>loading..</div>}
      {!this.state.error && !this.state.loading && this.state.quote ? <GameContent setPlaying={this.setPlaying} setDisabled={this.setDisabled} state={this.state}/> : <p>{this.state.error}</p> }
    
      </div>)
  }
}

class GameContent extends React.Component {
  constructor(props) {
    super(props)
    this.state = props.state
    this.handleClick = this.handleClick.bind(this)
    this.doCountDown = this.doCountDown.bind(this)

  }
  
  handleClick (e) {
    const answerUsername = e.target.value
    const answerUserid = e.target.name
    this.checkAnswer(answerUsername, answerUserid)
  }

  checkAnswer(answerUsername, answerUserid) {
    axios.post("/answerCheck", 
    {
      params: {
      answer: answerUserid
    }
  }).then(response => {
    this.setState({
      correct: response.data.correct,
      playing: false,
      userGuess: answerUsername // In the database, these are stored as names instead of userids.. can"t remember why
    })
    this.saveResult()
    }
  )
  }

  addLegendaryQuote() {
    this.props.setDisabled(true)
    axios.post("/addLegendaryQuote", 
    {
      params: {
      userid: this.state.user.id,
      messageid: this.state.quote.message_id,
    }
  }).then((response) => {
    this.setState({response:response.data.result})
    this.props.setDisabled(false)
  })
  }

  componentDidMount() {
    if (this.state.playing) {
      this.doCountDown()
    }
  }

  // Add a listener to prevent browser page refresh
  componentWillMount() {
    onbeforeunload = e => {
      this.setState({userGuess: ''})
      this.saveResult()
    }
  }

  // Clear listener
  componentWillUnmount() {
    onbeforeunload = null
  }

  doCountDown() {
    this.setState({counterEnabled: true})
    let milliseconds = 9000
    let timer = setInterval(() => {
      if (!this.state.playing) {
        this.setState({counterEnabled: false})
        clearInterval(timer)
        return
      }
      if (this.state.seconds == 0) {
        this.setState({counterEnabled: false, gameOver: true, playing:false, disabled: true})
        clearInterval(timer)
        this.checkAnswer('','')
        return
      }
        this.setState({seconds: (milliseconds / 1000)})
        milliseconds -= 1000
      }, 1000)
    
  }

  saveResult() {
    axios.post("/addResult", 
    {
      params: {
        userid: this.state.user.id,
        messageid: this.state.quote.message_id,
        quote: this.state.quote.content,
        quoteAuthor: this.state.quote.username,
        userGuess: this.state.userGuess
      }
  }).then(() => {

    this.props.setPlaying(false)
  })
  }

  render() {
    if (this.state.loading) {
      return(<div>loading..</div>)
    }
    return(
      <div>
      <p><b>Who said the following: </b></p>
      <p>{this.state.quote.content}</p>
      {this.state.availableWhoSaiditUsers.map((user) =>  <input type="button" className={(this.state.availableWhoSaiditUsers.indexOf(user) % 2) === 0 ? "whosaiditChoiceButtonBlue" : "whosaiditChoiceButtonBlack"} 
            disabled={(!this.state.playing || this.state.disabled) && "true"} id="gameStartButton1" name={user.user_id} value={user.name} onClick={(data) => this.handleClick(data)}></input>)}  
      {!this.state.gameOver && this.state.correct === true && <p><font color="Green">Correct!</font> It was <b>{this.state.quote.username}</b> on {new Date(moment(this.state.quote.ts)).toUTCString()}</p>}
      {!this.state.gameOver && this.state.correct === false && <p><font color="Red">Wrong!</font> It was <b>{this.state.quote.username}</b> on {new Date(moment(this.state.quote.ts)).toUTCString()}</p>}
      {this.state.gameOver && <p>Time is up! It was <b>{this.state.quote.username}</b> on {new Date(moment(this.state.quote.ts)).toUTCString()}</p>}
      {(this.state.correct === true || this.state.correct === false) && <input type="button" disabled={this.state.response && "true"} value="Mark this quote as a legendary quote" onClick={() => this.addLegendaryQuote()} className="whosaiditChoiceButtonBlue" />}
      {this.state.response && <p>{this.state.response}</p>}
      {<h2>{this.state.seconds}</h2>}
      </div>)
  }
}


module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
