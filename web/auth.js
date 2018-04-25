const express = require("express")
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
  app.get("/login", passport.authenticate("discord", {scope, failureRedirect: "/error"}), (req, res) => {
    res.redirect("/")
  })
}

module.exports = {init, requireAdmin, requireLogin}
