const passport = require("passport")
const DiscordStrategy = require("passport-discord").Strategy
const session = require("express-session")
const redis = require("redis")
const RedisStore = require("connect-redis")(session)

const redisClient = redis.createClient({
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT,
})
//const redisOptions = {
//}

const ADMIN_USER_IDS = (process.env.ADMIN_USER_IDS || "").split(",")
const ALLOWED_WHOSAIDIT_USERIDS = ADMIN_USER_IDS.concat([
  "210182155928731649", // Thomaxius#3355
  "141234778564198401", // Oikz#5960
  "141794093133987840", // Snagu#8069
  "236602023225720832", // Nauta#9321
  "141649488069656576", // rce#9389
  "138256165640339457", // RED#1000
  "141816757483470848", // daksu#2007
  "155798687103057921", // Emmi#0007
  "140917453302661121", // niske#0349
  "252237804803719168", // Nanbites#2365
  "66152978838466560", // Faireal#0031
  "141950807363813377", // Veli Murmeli#0655
  "511494027481186317", // Emm1h#7182
])

const requireLogin = (req, res, next) => {
  if (!req.isAuthenticated()) {
    console.log("requireLogin: no auth")
    return res.redirect("/login")
  }
  return next()
}

const requireAdmin = (req, res, next) => {
  if (!req.isAuthenticated()) {
    console.log("requireAdmin: no auth")
    return res.redirect("/login")
  }

  if (!ADMIN_USER_IDS.includes(req.user.id)) {
    console.log("requireAdmin: no admin")
    // TODO: Error page
    return res.sendStatus(403)
  }

  return next()
}

const requirePlayingClearance = (req, res, next) => {
  if (!req.isAuthenticated()) {
    console.log("requirePlayingClearance: no auth")
    return res.redirect("/login")
  }

  if (!ALLOWED_WHOSAIDIT_USERIDS.includes(req.user.id)) {
    console.log("requirePlayingClearance: Userid is not allowed to play.")
    // TODO: Error page
    return res.sendStatus(403)
  }

  return next()
}

const init = app => {
  const scope = ["identify"]

  passport.serializeUser((user, done) => done(null, user))
  passport.deserializeUser((obj, done) => done(null, obj))

  passport.use(new DiscordStrategy({
    clientID: process.env.DISCORD_CLIENT_ID,
    clientSecret: process.env.DISCORD_CLIENT_SECRET,
    callbackURL: process.env.DISCORD_CALLBACK_URL,
    scope: scope,
  }, (accessToken, refreshToken, profile, done) => {
    console.log(`Logged in as ${JSON.stringify(profile.id, null, 2)}`)
    process.nextTick(() => done(null, profile))
  }))

  app.use(session({
    store: new RedisStore({
      client: redisClient,
      prefix: "web:session:",
    }),
    secret: process.env.WEB_SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
  }))

  app.use(passport.initialize())
  app.use(passport.session())

  app.get("/logout", (req, res) => {
    console.log("Logging out")
    req.logout()
    res.redirect("/")
  })
  app.get("/login", passport.authenticate("discord", { scope, failureRedirect: "/error" }), (req, res) => {
    res.redirect("/")
  })
}

module.exports = { init, requireAdmin, requireLogin, requirePlayingClearance }
