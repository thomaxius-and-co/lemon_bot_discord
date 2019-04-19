const parseUrl = require("url").parse
const https = require("https")
const zlib = require("zlib")
const splitMessage = require("./split.js")

const AWS = require("aws-sdk")
AWS.config.update({ region: "eu-west-1" })
const SecretsManager = new AWS.SecretsManager({ apiVersion: "2017-10-17" })

const MAX_MESSAGE_LENGTH = 2000 - "``````".length

exports.handler = async function(event, context) {
  const DISCORD_WEBHOOK_URL = await fetchSecretWebhookUrl()
  console.log("Handling event:", JSON.stringify(event, null, 2))
  const payload = await gunzipObj(event.awslogs.data)
  console.log("Payload:", JSON.stringify(payload, null, 2))

  if (payload.messageType === "DATA_MESSAGE") {
    for (const e of payload.logEvents) {
      const lines = e.message.split("\n")
      const messages = splitMessage(lines, "\n", MAX_MESSAGE_LENGTH)
      for (const msg of messages) {
        const data = {
          username: "Errors",
          icon_url: "https://rce.fi/error.png",
          text: "```" + msg + "```",
        }
        await post(DISCORD_WEBHOOK_URL + "/slack", data)
      }
    }
  }
}

async function gunzipObj(base64data) {
  const bytes = Buffer.from(base64data, "base64")
  const json = await gunzip(bytes)
  return JSON.parse(json)
}

async function gunzip(buf) {
  return new Promise((resolve, reject) => {
    zlib.gunzip(buf, function(err, result) {
      if (err) {
        reject(err)
      } else {
        resolve(result)
      }
    })
  })
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
  return response.data.SecretString
}
