const passport = require("passport")
const DiscordStrategy = require("passport-discord").Strategy
const session = require("express-session")
const RedisStore = require("connect-redis")(session)

const redisOptions = {
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT,
  prefix: "web:session:",
  logErrors: true,
}

const ADMIN_USER_IDS = (process.env.ADMIN_USER_IDS || "").split(",")
const ALLOWED_WHOSAIDIT_USERIDS = (process.env.ALLOWED_WHOSAIDIT_USERIDS || process.env.ADMIN_USER_IDS + ",210182155928731649,141234778564198401,141794093133987840,236602023225720832,141649488069656576,138256165640339457,141816757483470848,155798687103057921,140917453302661121,252237804803719168,66152978838466560,141950807363813377,511494027481186317").split(",")

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
    store: new RedisStore(redisOptions),
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
