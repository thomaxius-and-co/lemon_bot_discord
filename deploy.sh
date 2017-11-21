#!/bin/bash

ROOT="$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")"
cd $ROOT

set -o errexit
trap "rm vault.pw" SIGINT SIGTERM EXIT

echo $ANSIBLE_VAULT_PASSWORD > vault.pw

set +o errexit
export NVM_DIR="$ROOT/.nvm"
source "$ROOT/web/nvm.sh"
set -o errexit
nvm install

ANSIBLE_CONFIG="$ROOT/ansible/ansible.cfg" \
ANSIBLE_LIBRARY="$ROOT/ansible/library" \
ansible-playbook \
  --vault-password-file=vault.pw \
  --extra-vars=@ansible/secrets.yml \
  ansible/deploy.yml
