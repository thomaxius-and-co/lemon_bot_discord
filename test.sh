#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")

set -e
ansible-playbook --syntax-check ansible/deploy.yml
