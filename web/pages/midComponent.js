const Promise = require('bluebird')
const pgp = require('pg-promise')({ promiseLib: Promise })
const {distinct} = require('../util.js')
const {getNiskeElo} = require('../db.js')

module.exports = {
    getNiskeElo
}