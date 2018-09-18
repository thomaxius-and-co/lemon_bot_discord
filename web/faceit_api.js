
const request = require('request-promise')
const faceit_api = process.env.FACEIT_API_KEY

function getStats(playerGuid) {
    return request({
      headers: {Authorization: "Bearer " + faceit_api},
      method: 'GET',
      uri: `https://open.faceit.com/data/v4/players/${playerGuid}/stats/csgo`,
      json: true,
    })
  }

module.exports = {getStats}