#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")

db_name="lemon"
vagrant ssh -c "sudo -u postgres psql $db_name"
