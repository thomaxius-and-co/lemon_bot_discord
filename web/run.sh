#!/bin/sh

set -e

mkdir -p .generated
npm install --only=production
npm run build-client
npm run start
