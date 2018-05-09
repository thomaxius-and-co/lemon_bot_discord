const request = require('request-promise')
const {db} = require('./db')

function setup(app) {
  app.get('/auth/nokia', redirectToNokiaHealth)
  app.get('/auth/nokia/callback', handleCallback)
}

function getDevice(userId) {
  return db.query(`select access_token, refresh_token from nokia_health_link where user_id = $1`, [userId]).then(rows => {
    if (rows.length === 0) {
      // No access token available for the user
      return undefined
    }

    const accessToken = rows[0].access_token
    const refreshToken = rows[0].refresh_token
    const options = {
      method: 'GET',
      uri: `https://api.health.nokia.com/v2/user?action=getdevice&access_token=${accessToken}`,
      json: true,
    }
    return request(options).then(json => {
      if (json.status === 401) {
        console.log(`User access_token might be expired. Refresh the access token and try again.`)
        return refreshAccessToken(userId, refreshToken).then(() => request(options))
      }
      return json
    })
  })
}

function refreshAccessToken(userId, refreshToken) {
  return request({
    url: `https://account.health.nokia.com/oauth2/token`,
    method: 'POST',
    form: makeRefreshRequest(refreshToken),
    json: true,
  }).then(response => {
    console.log(`Refreshed Nokia Health access token`)
    return upsertToken(userId, response)
  })
}

function redirectToNokiaHealth(req, res) {
  // TODO: If user already has Nokia Health link this might not be required (unless token is expired?)
  req.session.nokia_state = `thisshouldprobablybesomethingrandombutnotnecessarilysecret`
  res.redirect(makeAuthorizeUrl(req.session.nokia_state))
}

function handleCallback(req, res) {
  if (req.query.state !== req.session.nokia_state) {
    console.log(`State '${req.query.state}' does not match what was given on redirect (${req.session.nokia_state})`)
    // TODO: Some proper flow for this error case
    return res.send(500, 'Internal server error')
  }

  console.log(`Received code from Nokia Health`)

  request({
    url: `https://account.health.nokia.com/oauth2/token`,
    method: 'POST',
    form: makeTokenRequest(req.query.code),
    json: true,
  }).then(response => {
    console.log(`Received access token from Nokia Health`)
    upsertToken(req.user.id, response).then(() => res.redirect('/'))
  })
}

function upsertToken(userId, tokenResponse) {
  const sql = `
    INSERT INTO nokia_health_link (user_id, access_token, refresh_token, original, changed, created)
    VALUES ($1, $2, $3, $4, current_timestamp, current_timestamp)
    ON CONFLICT (user_id) DO UPDATE SET
      access_token = EXCLUDED.access_token,
      refresh_token = EXCLUDED.refresh_token,
      original = EXCLUDED.original,
      changed = current_timestamp
  `
  const params = [userId, tokenResponse.access_token, tokenResponse.refresh_token, JSON.stringify(tokenResponse)]
  return db.query(sql, params)
}

function makeAuthorizeUrl(state) {
  const responseType = `code`
  const clientId = process.env.NOKIA_HEALTH_CLIENT_ID
  const scope = `user.info,user.metrics,user.activity`
  const redirectUri = process.env.NOKIA_HEALTH_CALLBACK_URL
  return `https://account.health.nokia.com/oauth2_user/authorize2` +
    `?response_type=${responseType}` +
    `&client_id=${clientId}` +
    `&state=${state}` +
    `&scope=${scope}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}`
}

function makeTokenRequest(code) {
  return {
    'grant_type': `authorization_code`,
    'client_id': process.env.NOKIA_HEALTH_CLIENT_ID,
    'client_secret': process.env.NOKIA_HEALTH_CLIENT_SECRET,
    'code': code,
    'redirect_uri': process.env.NOKIA_HEALTH_CALLBACK_URL,
  }
}

function makeRefreshRequest(refreshToken) {
  return {
    'grant_type': `refresh_token`,
    'client_id': process.env.NOKIA_HEALTH_CLIENT_ID,
    'client_secret': process.env.NOKIA_HEALTH_CLIENT_SECRET,
    'refresh_token': refreshToken,
  }
}

module.exports = {
  setup,
  getDevice,
}
