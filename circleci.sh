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
  zip \
  build-essential git python-minimal python-pip findutils python3-minimal python3-dev

curl https://bootstrap.pypa.io/get-pip.py | python3.8
pip install -r ansible/requirements.txt > /dev/null

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
