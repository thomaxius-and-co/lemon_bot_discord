function distinct(xs) {
  return Array.from(new Set(xs))
}

function copy(x) {
  return JSON.parse(JSON.stringify(x))
}

module.exports = {
  distinct,
  copy,
}
