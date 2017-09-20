const React = require('react')
const moment = require('moment')
require('moment-timezone')

const pageTitle = 'Discord Admin'

const initialState = {
  user: {},
}

const renderPage = state =>
  <div>
    <h1>Discord Admin</h1>
    <p>You are logged in as user:</p>
    <pre>{JSON.stringify(state.user, null, 2)}</pre>
  </div>

module.exports = {
  pageTitle,
  initialState,
  renderPage,
}
