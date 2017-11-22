#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")"/scripts/common

function run_bot {
  source "$ROOT/secrets"
  TZ=UTC python -u "$ROOT/src/run_lemon_bot.py"
}

check_dependencies
start_vm
init_virtualenv
syntax_check
run_bot
