module.exports = function splitMessage(pieces, limit) {
  // Message is OK
  const joined = pieces.join("\n")
  if (joined.length <= limit) {
    return [joined]
  }

  // One piece left? Force split at limit
  if (pieces.length == 1) {
    const p = pieces[0]
    return [
      p.slice(0, limit),
      ...splitMessage([p.slice(limit, p.length)], limit),
    ]
  }

  // Normal split in the middle
  const [a, b] = splitList(pieces)
  return [
    ...splitMessage(a, limit),
    ...splitMessage(b, limit),
  ]
}

function splitList(xs) {
  const mid = Math.floor(xs.length / 2)
  return [xs.slice(0, mid), xs.slice(mid, xs.length)]
}
