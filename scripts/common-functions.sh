#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail
readonly repo="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

readonly PIPENV_VERSION="2021.11.5.post0"
readonly PYTHON_VERSION="3.9.1"

function setup_aws {
  if ! running_on_github_actions; then
    export AWS_PROFILE="discord-$ENV"
  fi
  export AWS_CONFIG_FILE="$repo/scripts/lib/aws_config"
  export AWS_REGION="eu-west-1"
  export AWS_DEFAULT_REGION="$AWS_REGION"

  aws sts get-caller-identity
  AWS_ACCOUNT_ID="$( aws sts get-caller-identity --query Account --output text )"
  export AWS_ACCOUNT_ID
}

function require_docker {
  require_command docker
  docker ps > /dev/null 2>&1 || {
    fatal "Running 'docker ps' failed. Is docker daemon running? Aborting."
  }
}

function docker_run_with_aws_env {
  docker run \
    --env AWS_PROFILE \
    --env AWS_REGION \
    --env AWS_DEFAULT_REGION \
    --env AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY \
    --env AWS_SESSION_TOKEN \
    --env AWS_CONFIG_FILE=/aws_config \
    --volume "$AWS_CONFIG_FILE:/aws_config" \
    --volume "$HOME/.aws:/root/.aws" \
    "$@"
}

function aws {
  docker_run_with_aws_env \
    --volume "$( pwd ):/aws" \
    --rm -i amazon/aws-cli:2.0.6 "$@"
}

function running_on_github_actions {
  [ "${GITHUB_ACTION:-}" != "" ]
}

function init_node {
  set +o errexit +o nounset
  export NVM_DIR="$HOME/.cache/nvm"
  source "$repo/scripts/lib/nvm.sh"
  nvm install "18"
  set -o errexit -o nounset
}


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
