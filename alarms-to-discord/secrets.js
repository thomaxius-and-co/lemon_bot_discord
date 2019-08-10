const AWS = require("aws-sdk")

AWS.config.update({ region: "eu-west-1" })

const SecretsManager = new AWS.SecretsManager({
  apiVersion: "2017-10-17",
})

function mkSecret(secretId) {
  let _cache = undefined

  function clear() {
    _cache = undefined
  }

  async function get() {
    if (_cache) return _cache

    _cache = getSecretValue(secretId)
    return _cache
  }

  return { get, clear }
}

async function getSecretValue(secretId) {
  const response = await SecretsManager.getSecretValue({
    SecretId: secretId,
    VersionStage: "AWSCURRENT",
  }).promise()
  return response.SecretString
}

module.exports = { mkSecret }
