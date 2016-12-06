#!/bin/bash

set -e
cd $(dirname "${BASH_SOURCE[0]}")

vagrant ssh -c "journalctl -u lemon -n 100 -f"
