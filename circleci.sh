#!/usr/bin/env bash
source "$( dirname "${BASH_SOURCE[0]}" )/scripts/common-functions.sh"

function main {
  # For add-apt-repository
  apt-get -q update
  apt-get -q install -y software-properties-common

  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get -q update

  apt-get -q install -y \
    python3.9 python3.9-dev \
    libxml2-dev libxslt1-dev zlib1g-dev \
    curl zip \
    build-essential git python-minimal python-pip findutils python3-minimal python3-dev

  install_pyenv

  # Workaround for issues with pip/python 2 and UTF-8
  export LC_ALL="C.UTF-8"

  run_tests
  ./journald-cloudwatch/build.sh
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
}

function install_pyenv {
  curl https://pyenv.run | bash
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
}

main "$@"
