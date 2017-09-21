const React = require("react")

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
      {page.renderPage(applicationState)}
    </body>
  </html>

module.exports = render
