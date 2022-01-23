const request = require('request-promise')
const {db} = require('./db')
const { v4: uuid } = require('uuid')

const API_HOSTNAME = `wbsapi.withings.net`
const AUTH_HOSTNAME = `account.withings.com`
const enabled = (!!process.env.WITHINGS_CLIENT_SECRET && !!process.env.WITHINGS_CLIENT_ID)

function setup(app) {
  if (enabled) {
    app.get(`/auth/withings`, redirectToAuth)
    app.get(`/auth/withings/callback`, handleCallback)
  }
  else {
    console.log('User has not set up withings client id and\or token')
    return undefined
  }
}

function getDevice(userId) {
  return getTokens(userId).then(tokens => {
    if (!tokens) {
      // No access token available for the user
      console.log("No tokens")
      return undefined
    }

    const accessToken = tokens.access_token
    return request({
      method: 'GET',
      uri: `https://${API_HOSTNAME}/v2/user?action=getdevice&access_token=${accessToken}`,
      json: true,
    })
  })
}

function refreshAccessToken(userId) {
  return getTokens(userId).then(tokens =>
    request({
      url: `https://${API_HOSTNAME}/oauth2`,
      method: 'POST',
      form: makeRefreshRequest(tokens.refresh_token),
      json: true,
    }).then(response => {
      console.log(`Refreshed Withings access token`)
      return upsertToken(userId, response.body)
    })
  )
}

function redirectToAuth(req, res) {
  // TODO: If user already has account linked this might not be required (unless token is expired?)
  req.session.withings_state = uuid()
  res.redirect(makeAuthorizeUrl(req.session.withings_state))
}

function handleCallback(req, res) {
  if (req.query.state !== req.session.withings_state) {
    console.log(`State '${req.query.state}' does not match what was given on redirect (${req.session.withings_state})`)
    // TODO: Some proper flow for this error case
    return res.send(500, 'Internal server error')
  }

  console.log(`Received code from Withings`)

  request({
    url: `https://${API_HOSTNAME}/oauth2`,
    method: 'POST',
    form: makeTokenRequest(req.query.code),
    json: true,
  }).then(response => {
    console.log(`Received access token from Withings`)
    upsertToken(req.user.id, response.body).then(() => res.redirect('/'))
  })
}

function upsertToken(userId, tokenResponse) {
  const sql = `
    INSERT INTO withings_link (user_id, access_token, refresh_token, original, changed, created)
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
  const clientId = process.env.WITHINGS_CLIENT_ID
  const scope = `user.info,user.metrics,user.activity`
  const redirectUri = process.env.WITHINGS_CALLBACK_URL
  return `https://${AUTH_HOSTNAME}/oauth2_user/authorize2` +
    `?response_type=${responseType}` +
    `&client_id=${clientId}` +
    `&state=${state}` +
    `&scope=${scope}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}`
}

function makeTokenRequest(code) {
  return {
    'grant_type': `authorization_code`,
    'client_id': process.env.WITHINGS_CLIENT_ID,
    'client_secret': process.env.WITHINGS_CLIENT_SECRET,
    'code': code,
    'redirect_uri': process.env.WITHINGS_CALLBACK_URL,
  }
}

function makeRefreshRequest(refreshToken) {
  return {
    'grant_type': `refresh_token`,
    'client_id': process.env.WITHINGS_CLIENT_ID,
    'client_secret': process.env.WITHINGS_CLIENT_SECRET,
    'refresh_token': refreshToken,
  }
}

function autoRefreshTokens(func) {
  if (enabled) {
    return function(userId, ...args) {
      return func(userId, ...args).then(json => {
        if (json.status === 401) {
          console.log(`User access_token might be expired. Refresh the access token and try again.`)
          return refreshAccessToken(userId).then(() => func(userId, ...args))
        }
        return json
      })
  }
}
}

function getTokens(userId) {
  return db.query(`select access_token, refresh_token from withings_link where user_id = $1`, [userId]).then(head)
}

function head(xs) {
  return xs.length > 0 ? xs[0] : undefined
}

module.exports = {
  setup,
  getDevice: autoRefreshTokens(getDevice),
  enabled
}
