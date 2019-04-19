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

discord_alarm_webhook_secret_arn="$(aws secretsmanager describe-secret --secret-id discord-alarm-webhook --query ARN --output text)"

ANSIBLE_CONFIG="$ROOT/ansible/ansible.cfg" \
ANSIBLE_LIBRARY="$ROOT/ansible/library" \
ansible-playbook \
  --vault-password-file=vault.pw \
  --extra-vars=@ansible/secrets.yml \
  --extra-vars "discord_alarm_webhook_secret_arn=$discord_alarm_webhook_secret_arn" \
  ansible/deploy.yml
