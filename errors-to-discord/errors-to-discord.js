const parseUrl = require("url").parse
const https = require("https")
const zlib = require("zlib")

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL

exports.handler = async function(event, context) {
  log("Handling event:", event)
  const payload = await gunzipObj(event.awslogs.data)
  log("Payload:", payload)

  if (payload.messageType === "DATA_MESSAGE") {
    const {logEvents} = payload
    const logMessages = payload.logEvents.map(e => e.message)
    for (const e of logEvents) {
      const data = {
        username: "Errors",
        icon_url: "https://rce.fi/error.png",
        text: "```" + e.message + "```",
      }
      await post(DISCORD_WEBHOOK_URL + "/slack", data)
    }
  }

  context.succeed()
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

async function post(url, data) {
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

function log(...args) {
  const timestamp = (new Date()).toISOString()
  const strings = args.map(_ => typeof _ === "object" ? JSON.stringify(_, null, 2) : String(_))
  console.log(timestamp, ...strings)
}
