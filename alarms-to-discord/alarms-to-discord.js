const parseUrl = require("url").parse
const https = require("https")

const AWS = require("aws-sdk")
AWS.config.update({ region: "eu-west-1" })
const SecretsManager = new AWS.SecretsManager({ apiVersion: "2017-10-17" })

const Colors = {
  Red: 0xCC0000,
  Green: 0x009933,
  Yellow: 0xE07700,
  Gray: 0xE0E0E0,
}

exports.handler = async function(event) {
  const DISCORD_WEBHOOK_URL = await fetchSecretWebhookUrl()
  console.log("Handling event", JSON.stringify(event, null, 2))
  const messages = event.Records.map(_ => JSON.parse(_.Sns.Message))

  const messagePayloads = messages.map(({AlarmName, NewStateReason, NewStateValue}) => {
    const color = NewStateValue == "ALARM" ? Colors.Red :
      NewStateValue == "INSUFFICIENT_DATA" ? Colors.Yellow :
      NewStateValue == "OK" ? Colors.Green : Colors.Gray
    return {embeds: [{title: AlarmName, description: NewStateReason, color}]}
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

async function fetchSecretWebhookUrl() {
  const response = await SecretsManager.getSecretValue({
    SecretId: "discord-alarm-webhook",
    VersionStage: "AWSCURRENT",
  }).promise()
  return response.SecretString
}
