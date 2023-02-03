#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")"/scripts/common-functions.sh

function run_web {
  pushd "$ROOT/web"
  npm install
  source "$ROOT/secrets"
  npm run dev
  popd
}

start_vm
init_node
run_web
