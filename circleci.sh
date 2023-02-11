#!/usr/bin/env bash
source "$( dirname "${BASH_SOURCE[0]}" )/scripts/common-functions.sh"

function main {
  apt-get -q update

  apt-get -q install -y \
    libxslt1-dev zip git findutils docker

  install_pyenv

  # Workaround for issues with pip/python 2 and UTF-8
  export LC_ALL="C.UTF-8"

  run_tests
  ./deploy.sh
}

function run_tests {
  set_python_version
  install_python_dependencies

  cd "$repo"
  DATABASE_HOST="localhost" \
  DATABASE_PORT="5432" \
  DATABASE_NAME="lemon" \
  DATABASE_USERNAME="lemon" \
  DATABASE_PASSWORD="lemon" \
  REDIS_HOST="localhost" \
  REDIS_PORT="6379" \
  python -m pytest

  deactivate
}

function install_pyenv {
  # https://github.com/pyenv/pyenv/wiki#suggested-build-environment
  apt-get -q install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev

  curl https://pyenv.run | bash
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
}

main "$@"
