#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail
readonly repo="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

readonly PIPENV_VERSION="2021.11.5.post0"
readonly PYTHON_VERSION="3.9.1"

function set_python_version {
  info "Installing python version $PYTHON_VERSION"
  require_command pyenv

  pushd "$repo"
  eval "$( pyenv init --path )"
  pyenv install --skip-existing "$PYTHON_VERSION"
  pyenv local "$PYTHON_VERSION"
  popd
}

function install_python_dependencies {
  pushd "$repo"
  python -m pip install pipenv==${PIPENV_VERSION}
  python -m pipenv install --dev > /dev/null
  source "$( python -m pipenv --venv )/bin/activate"

  if [ "$( python --version )" != "Python $PYTHON_VERSION" ]; then
    info "Python version has changed; rebuilding virtualenv"
    deactivate
    python -m pipenv --rm
    install_python_dependencies
  fi
  popd
}

function require_command {
  if ! command -v "$1" > /dev/null; then
    fatal "Command '$1' is required"
  fi
}

function info {
  log "INFO" "$1"
}

function fatal {
  log "ERROR" "$1"
  exit 1
}

function log {
  local -r level="$1"
  local -r message="$2"
  local -r timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  >&2 echo -e "${timestamp} ${level} ${message}"
}