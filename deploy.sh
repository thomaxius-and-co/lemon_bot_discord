#!/bin/bash

export AWS_REGION="eu-west-1"
export AWS_DEFAULT_REGION="$AWS_REGION"

ROOT="$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")"
cd $ROOT

set -o errexit

set +o errexit
export NVM_DIR="$ROOT/.nvm"
source "$ROOT/web/nvm.sh"
set -o errexit
nvm install

discord_alarm_webhook_secret_arn="$(aws secretsmanager describe-secret --secret-id discord-alarm-webhook --query ARN --output text)"

ANSIBLE_CONFIG="$ROOT/ansible/ansible.cfg" \
ANSIBLE_LIBRARY="$ROOT/ansible/library" \
ansible-playbook \
  --vault-password-file=./get_vault_password.sh \
  --extra-vars=@ansible/secrets.yml \
  --extra-vars "discord_alarm_webhook_secret_arn=$discord_alarm_webhook_secret_arn" \
  ansible/deploy.yml
