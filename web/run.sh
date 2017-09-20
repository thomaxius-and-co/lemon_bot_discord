#!/bin/sh

set -e

npm config set progress false
jq -r '.dependencies | keys | join("\n")' package.json | xargs -n 1 npm install
npm run build-client
npm run start
