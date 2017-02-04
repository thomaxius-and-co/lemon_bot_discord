#!/bin/bash

set -e

dump_file="$(realpath "$1")"

cd $(dirname "${BASH_SOURCE[0]}")

if [ -z "$dump_file" ]; then
  echo "Usage $0 <input_file>"
  exit 1
fi

cat "$dump_file" | vagrant ssh -c "sudo -u postgres pg_restore -c -d lemon"
