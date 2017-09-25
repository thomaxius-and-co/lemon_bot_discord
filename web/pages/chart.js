const React = require("react")
const {findDOMNode} = require("react-dom")
let c3 // C3 is lazily loaded in componentDidMount because it doesn't run on server.

class LineChart extends React.Component {
  componentDidMount() {
    c3 = require("c3")
    const config = Object.assign({bindto: findDOMNode(this)}, this.props)
    this.chart = c3.generate(config)
    //this.chart.load(this.props.data)
  }

  componentWillUnmount() {
    this.chart.destroy()
  }

  render() {
    // Dummy element for rendering the chart
    return <div></div>
  }
}

module.exports = {LineChart}
