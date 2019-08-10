const parseUrl = require("url").parse
const https = require("https")

const { mkSecret } = require("./secrets.js")

const secretWebhookUrl = mkSecret("discord-alarm-webhook")

exports.handler = async function(event) {
  console.log("Handling event", JSON.stringify(event, null, 2))
  const messages = event.Records.map(_ => JSON.parse(_.Sns.Message))

  const messagePayloads = messages.map(({AlarmName, NewStateReason}) => {
    return {embeds: [{title: AlarmName, description: NewStateReason, color: 0xff0000}]}
  })

  for (const data of messagePayloads) {
    const webhookUrl = await secretWebhookUrl.get()
    const {res} = await post(webhookUrl + "/slack", data)
    if (res.statusCode !== 200) {
      secretWebhookUrl.clear()
      throw new Error("Failed to post message. Cleared cached webhook URL in case it has changed")
    }
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
        resolve({ res, body: result })
      })
    })
    req.on("error", reject)
    req.write(JSON.stringify(data))
    req.end()
  })
}
