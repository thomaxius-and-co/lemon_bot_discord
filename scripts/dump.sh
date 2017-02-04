#!/bin/bash

set -e

env="${1:-local}"
ssh_command="echo"
if [ $env = "local" ]; then
  ssh_command="vagrant ssh -c"
elif [ $env = "prd" ]; then
  ssh_command="ssh -t lemon"
fi

dump_file="$(realpath "$2")"

cd $(dirname "${BASH_SOURCE[0]}")

if [ -z "$dump_file" ]; then
  echo "Usage $0 <env> <output_file>"
  exit 1
fi

$ssh_command "sudo -iu postgres pg_dump -Fc lemon" > "$dump_file"
