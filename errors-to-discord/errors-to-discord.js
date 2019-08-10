const parseUrl = require("url").parse
const https = require("https")
const zlib = require("zlib")
const splitMessage = require("./split.js")

const { mkSecret } = require("./secrets.js")

const secretWebhookUrl = mkSecret("discord-alarm-webhook")

const MAX_MESSAGE_LENGTH = 2000 - "``````".length

exports.handler = async function(event, context) {
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
        const webhookUrl = await secretWebhookUrl.get()
        const {res} = await post(webhookUrl + "/slack", data)
        if (res.statusCode !== 200) {
          secretWebhookUrl.clear()
          throw new Error("Failed to post message. Cleared cached webhook URL in case it has changed")
        }
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
        resolve({ res, body: result })
      })
    })
    req.on("error", reject)
    req.write(JSON.stringify(data))
    req.end()
  })
}
