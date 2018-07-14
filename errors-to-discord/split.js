module.exports = function splitMessage(pieces, joinStr, limit) {
  // Message is OK
  const joined = pieces.join(joinStr)
  if (joined.length <= limit) {
    return [joined]
  }

  // One piece left? Force split at limit
  if (pieces.length == 1) {
    const p = pieces[0]
    return [
      p.slice(0, limit),
      ...splitMessage([p.slice(limit, p.length)], joinStr, limit),
    ]
  }

  // Normal split in the middle
  const [a, b] = splitList(pieces)
  return [
    ...splitMessage(a, joinStr, limit),
    ...splitMessage(b, joinStr, limit),
  ]
}

function splitList(xs) {
  const mid = Math.floor(xs.length / 2)
  return [xs.slice(0, mid), xs.slice(mid, xs.length)]
}
