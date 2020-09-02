const React = require('react')
require('moment-timezone')

const axios = require("axios")

const pageTitle = 'Quotes'

const initialState = {
  sensibleQuotes: []
}

const isTrue = str => str === 'true';

const bulkAddLegendaryQuotes = (toBeAddedLegendaryQuotes, user) => {
  axios.post("/bulkAddLegendaryQuotes",
    {
      params: {
        user: user,
        messageIds: toBeAddedLegendaryQuotes,
      }
    })
}

const Page = (props) => {
  const { sensibleQuotes, user } = props.state
  let toBeAddedLegendaryQuotes = [];

  const handleFormSubmit = formSubmitEvent => {
    formSubmitEvent.preventDefault();
    bulkAddLegendaryQuotes(toBeAddedLegendaryQuotes, user)
    toBeAddedLegendaryQuotes = [];
    alert("Quotes added. Possibly. Now forced reload.")
    window.location.reload(false);
  }


  const handleCheckboxChange = changeEvent => {
    const { id, } = changeEvent.target;
    if (toBeAddedLegendaryQuotes.indexOf(id) !== -1) {
      toBeAddedLegendaryQuotes = [...toBeAddedLegendaryQuotes.filter((quoteId) => quoteId !== id)];
    } else {
      toBeAddedLegendaryQuotes.push(id)
    }
  };

  return (
    <div>
      <div className="row">
        <h1>Server quotes</h1>
      </div>
      <form onSubmit={handleFormSubmit}>
        <button className="btn btn-default" type="submit">Add legendary quotes</button>
        <table className="row">
          <thead>
            <tr>
              <td>Name</td>
              <td>Content</td>
              <td>Mark as legendary</td>
            </tr>
          </thead>
          <tbody>
            {sensibleQuotes.map(x =>
              <tr key={x.epoch}>
                <td className="name">{x.username}</td>
                <td>{x.content}</td>
                <td><input type="checkbox" disabled={isTrue(x.is_legendary)} id={x.message_id} onChange={handleCheckboxChange}></input></td>
              </tr>
            )}
          </tbody>
        </table>
      </form>
    </div >)
}

const renderPage = state => [<Page state={state} />]


module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
