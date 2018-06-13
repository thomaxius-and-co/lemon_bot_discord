const parseUrl = require("url").parse
const https = require("https")

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL

exports.handler = async function(event) {
  console.log("Handling event", JSON.stringify(event, null, 2))
  const messages = event.Records.map(_ => JSON.parse(_.Sns.Message))

  const messagePayloads = messages.map(({AlarmName, NewStateReason}) => {
    return {embeds: [{title: AlarmName, description: NewStateReason, color: 0xff0000}]}
  })

  for (const data of messagePayloads) {
    await post(DISCORD_WEBHOOK_URL, data)
  }
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
        console.log("POST", url, res.statusCode, JSON.stringify(data, null, 2), result)
        resolve(result)
      })
    })
    req.on("error", reject)
    req.write(JSON.stringify(data))
    req.end()
  })
}
