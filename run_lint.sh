#!/usr/bin/env bash
source "$( dirname "${BASH_SOURCE[0]}" )/scripts/common-functions.sh"

function main {
  cd "$repo"
  set_python_version
  install_python_dependencies

  cd "$repo/src"
  python -m pylint --rcfile "$repo/.pylintrc" ./*
}

main "$@"
