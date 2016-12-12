#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")

host="$1"
dump_file="$2"
db_name="lemon"

if [ -z "$host" ] || [ -z "$dump_file" ]; then
  echo "Usage $0 <host> <output_file>"
  exit 1
fi

ssh lemon -- sudo -u postgres pg_dump -Fc $db_name > "$dump_file"
