#!/bin/sh

set -e

npm config set progress false
npm install
npm run build-client
npm run start
