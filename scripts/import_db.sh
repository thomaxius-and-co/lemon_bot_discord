#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")

dump_file="$1"
db_name="lemon"

if [ -z "$dump_file" ]; then
  echo "Usage $0 <input_file>"
  exit 1
fi

cat "$dump_file" | vagrant ssh -c "sudo -u postgres pg_restore -c -d $db_name"
