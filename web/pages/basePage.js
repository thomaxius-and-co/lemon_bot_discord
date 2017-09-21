const React = require("react")

const Login = ({user}) =>
  <ul className="login">
    {user && <li><a href="/admin">Admin</a></li>}
    {user ? <li><a href="/logout">Logout</a></li>
          : <li><a href="/login">Login</a></li>}
  </ul>

const Header = ({user}) =>
  <div className="header-wrapper">
    <div className="header">
      <ul className="navigation">
        <li><a href="/">Home</a></li>
      </ul>
      <Login user={user} />
    </div>
  </div>

const render = (page, applicationState, checksums) =>
  <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>{page.pageTitle}</title>
      <script type="text/javascript" dangerouslySetInnerHTML={{__html: `window.CHECKSUMS = ${JSON.stringify(checksums)};`}}></script>
      <script async src={`bundle.js?checksum=${checksums.bundleJsChecksum}`}></script>
      <link rel="stylesheet" href={`style.css?checksum=${checksums.styleCssChecksum}`}/>
    </head>
    <body id="applicationState" data-state={JSON.stringify(applicationState)}>
      <Header user={applicationState.user} />
      <div className="content-wrapper">
        <div className="content">
          {page.renderPage(applicationState)}
        </div>
      </div>
    </body>
  </html>

module.exports = render
