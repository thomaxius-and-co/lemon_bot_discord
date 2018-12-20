
const db = require("./db")

let correctQuote = null

checkAnswer = (req, res, next) => {
  if (req.body.params.answer ==  this.correctQuote.user_id) {
    res.send({
      correct: true
    })
  }
  else {
    res.send({
      correct: false
    })
  }
}


removeEmojis = (quote) => quote.replace("<:", " <:").replace(">", "> ").split(" ").map((word) => (!(word.startsWith("<:") && word.endsWith(">")) ? word : "")).join(" ")  // Remove custom emojis from quote, such as <:feelsgood:236116066584100864>

fixMentions = async (quote) => {
    await db.getUserNamesAndIds().then((result) => {
    result.forEach((item) => {
      quote = quote.replace(`<@${item.user_id}>`, `@${item.name}`)
        })
    })
    return quote
    }

  sanitizeQuote = async (quote) => fixMentions(removeEmojis(quote))

function shuffle(array) { // Stolen from SO
  let counter = array.length

  while (counter > 0) {
      let index = Math.floor(Math.random() * counter)

      counter--

      let temp = array[counter]
      array[counter] = array[index]
      array[index] = temp
  }

  return array

}
function invalidQuote(quote) {
    function is_custom_emoji(quote) {
        return quote.startsWith("<:") && quote.endsWith(">")
    }
    function is_emoji(quote) {
        return quote.startsWith(":") && quote.endsWith(":")
    }
    function is_gibberish(quote) {
        return new Set(quote).size < 6
      }
    return is_gibberish(quote) || is_emoji(quote) || is_custom_emoji(quote)
}

check_quotes = async (quotes) => {
    for (quote of quotes) {
      const sanitizedQuote = await sanitizeQuote(String(quote.content))
      if (!invalidQuote(sanitizedQuote)) {
          quote.content = sanitizedQuote
        return quote
      }
      else {
        console.log("This quote is bad ", quote.content)
        continue
      }
  }
  return null
}

addResult = async (req, res, next) => {
  await db.saveWhosaiditHistory(req.body.params.userid, req.body.params.messageid, req.body.params.quote, req.body.params.quoteAuthor, req.body.params.userGuess).then(() => {
    res.send({
      success: true
    })
  })
}

addLegendaryQuote = async (req, res, next) => {
    await db.saveLegendaryQuote(req.body.params.messageid, req.body.params.userid).then((result) => {
          if (result) {
            res.send({
              result: "Legendary quote added succesfully!"
            })
          }
          else {
              res.send({
              result: "Legendary already exists."
            })
          }
  })
}
  

handleWhosaidit = async (req, res, next) => {
  db.getAvailableWhosaiditUsers("141649840923869184").then(availableUsersResult => {
    if (availableUsersResult.length < 5) {
        res.send({
          error: "Not enough users in the database to start a game."
        })
        return
      }
      db.getQuoteForWhosaidit("141649840923869184", availableUsersResult.map((user) => user.user_id)).then(async (quoteResult) => {
        const validQuote = await check_quotes(quoteResult)
        if (!validQuote) {
          res.send({
            error: "Not enough chat logged to play, try again later."
          })
          return
        }
        this.correctQuote = validQuote
        res.send({
          quote: validQuote,
          availableWhoSaiditUsers: shuffle(availableUsersResult)
        })
    }
    )
  }
  )
}

module.exports = {
    checkAnswer,
    addResult,
    handleWhosaidit,
    addLegendaryQuote
}