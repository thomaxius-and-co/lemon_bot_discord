#!/usr/bin/env bash

set -o errexit

apt-get update
apt-get install -y build-essential git python-minimal python-pip findutils python3-minimal
pip install -r ansible/requirements.txt
pip install tox==2.5.0

#./test.sh
./journald-cloudwatch/build.sh
./deploy.sh
