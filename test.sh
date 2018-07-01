#!/bin/bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"/scripts/common
cd $ROOT

set -o errexit

function cleanup {
  # Remove files generated by running tests
  find . -name "__pycache__" | xargs rm -rf
}

trap cleanup EXIT

function python_syntax_check {
  find src -name "*.py" | xargs python -m py_compile
}

function run_test {
  pip install -r "$ROOT/test-requirements.txt"
  pytest
}

ansible-playbook --syntax-check ansible/deploy.yml
check_dependencies
init_virtualenv "$(which python3.6)"
python_syntax_check
run_test
