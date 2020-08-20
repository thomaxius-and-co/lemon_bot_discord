#!/usr/bin/env bash

set -o errexit

# For add-apt-repository
apt-get -q update
apt-get -q install -y software-properties-common

add-apt-repository -y ppa:deadsnakes/ppa
apt-get -q update

apt-get -q install -y \
  python3.8 python3.8-dev \
  libxml2-dev libxslt1-dev zlib1g-dev \
  curl zip \
  build-essential git python-minimal python-pip findutils python3-minimal python3-dev

# Install pyenv for choosing any specific Python vversion
curl https://pyenv.run | bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

# Workaround for issues with pip/python 2 and UTF-8
export LC_ALL="en_US.UTF-8"

#DATABASE_HOST="localhost" \
#DATABASE_PORT="5432" \
#DATABASE_NAME="lemon" \
#DATABASE_USERNAME="lemon" \
#DATABASE_PASSWORD="lemon" \
#REDIS_HOST="localhost" \
#REDIS_PORT="6379" \
#./test.sh
./journald-cloudwatch/build.sh
./deploy.sh
