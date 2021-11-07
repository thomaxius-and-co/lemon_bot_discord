#!/usr/bin/env bash
source "$( dirname "${BASH_SOURCE[0]}" )/scripts/common-functions.sh"

function main {
  cd "$repo"
  set_python_version
  install_python_dependencies

  source "$repo/secrets"
  cd "$repo"
  python -m pytest_watch
}

main "$@"