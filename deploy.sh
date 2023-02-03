#!/bin/bash
set -o errexit -o nounset -o pipefail

repo="$( cd "$( dirname "$0" )" && pwd )"
source "$repo/scripts/common-functions.sh"

function main {
  export ENV="prod"
  export AWS_REGION="eu-west-1"
  export AWS_DEFAULT_REGION="$AWS_REGION"

  init_node
  setup_python_for_ansible
  setup_aws

  discord_alarm_webhook_secret_arn="$(aws secretsmanager describe-secret --secret-id discord-alarm-webhook --query ARN --output text)"

  cd "$repo/ansible"
  ANSIBLE_CONFIG="$repo/ansible/ansible.cfg" \
  ANSIBLE_LIBRARY="$repo/ansible/library" \
  ansible-playbook \
    --vault-password-file="$repo/get_vault_password.sh" \
    --extra-vars=@secrets.yml \
    --extra-vars "discord_alarm_webhook_secret_arn=$discord_alarm_webhook_secret_arn" \
    "$repo/ansible/deploy.yml"
}

function setup_python_for_ansible {
  export ANSIBLE_PYTHON_VERSION="3.9.1"
  pushd "$repo/ansible"
  #eval "$(pyenv init --path)"
  #pyenv install --skip-existing "$ANSIBLE_PYTHON_VERSION"
  #pyenv local "$ANSIBLE_PYTHON_VERSION"

  python3 -m pip install pipenv==2021.11.5.post0
  python3 -m pipenv install
  source "$(python3 -m pipenv --venv)/bin/activate"
  popd
}

main
