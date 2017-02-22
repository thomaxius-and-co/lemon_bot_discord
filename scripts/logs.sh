#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")

env="${1:-local}"
ssh_command="echo"
if [ $env = "local" ]; then
  ssh_command="vagrant ssh -c"
elif [ $env = "prd" ]; then
  ssh_command="ssh -t lemon"
fi

$ssh_command "journalctl -u lemon -n 100 -f"
