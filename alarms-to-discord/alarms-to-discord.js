const parseUrl = require("url").parse
const https = require("https")

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL

function log(...args) {
  const timestamp = (new Date()).toISOString()
  const strings = args.map(_ => typeof _ === "object" ? JSON.stringify(_, null, 2) : String(_))
  console.log(timestamp, ...strings)
}

function post(url, data) {
  return new Promise((resolve, reject) => {
    const {hostname, path} = parseUrl(url)
    const options = {
      hostname: hostname,
      path: path,
      port: 443,
      method: "POST",
      headers: {"Content-Type": "application/json"},
    }
    const req = https.request(options, res => {
      const chunks = []
      res.setEncoding("utf8")
      res.on("data", chunk => chunks.push(chunk))
      res.on("end", () => {
        const result = chunks.join("")

        log("POST", url, res.statusCode, data, result)
        resolve(result)
      })
    })
    req.on("error", reject)
    req.write(JSON.stringify(data))
    req.end()
  })
}

exports.handler = function(event, context) {
  log("Handling event", event)
  const messages = event.Records.map(_ => JSON.parse(_.Sns.Message))

  const promises = messages.map(({AlarmName, NewStateReason}) => {
    const data = {embeds: [{title: AlarmName, description: NewStateReason, color: 0xff0000}]}
    return post(DISCORD_WEBHOOK_URL, data)
  })
  Promise.all(promises)
    .then(results => {
      log("OK", results)
      context.succeed()
    })
    .catch(err => {
      log("ERROR", err)
      context.fail(err)
    })
}
