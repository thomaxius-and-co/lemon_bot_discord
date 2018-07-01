#!/usr/bin/env bash

set -o errexit

# For add-apt-repository
apt-get update
apt-get install -y software-properties-common

add-apt-repository ppa:deadsnakes/ppa
apt-get update

apt-get install -y \
  python3.6 \
  zip \
  build-essential git python-minimal python-pip findutils python3-minimal python3-dev
pip install -r ansible/requirements.txt

DATABASE_HOST="localhost" \
DATABASE_PORT="5432" \
DATABASE_NAME="lemon" \
DATABASE_USERNAME="lemon" \
DATABASE_PASSWORD="lemon" \
REDIS_HOST="localhost" \
REDIS_PORT="6379" \
./test.sh
./journald-cloudwatch/build.sh
./deploy.sh
