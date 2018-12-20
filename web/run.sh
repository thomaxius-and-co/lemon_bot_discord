#!/bin/sh

set -e

npm config set progress false

# Dirty hack :(
rm -f package-lock.json
rm -rf node_modules

npm install
npm run build-client
npm run start
