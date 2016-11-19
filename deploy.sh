#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")

set -e
trap "rm vault.pw" SIGINT SIGTERM EXIT

echo $ANSIBLE_VAULT_PASSWORD > vault.pw
ansible-playbook \
  --vault-password-file=vault.pw \
  --extra-vars=@ansible/secrets.yml \
  ansible/playbook.yml
