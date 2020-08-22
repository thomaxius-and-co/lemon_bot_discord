#!/bin/bash
set -o errexit -o nounset -o pipefail

repo="$( cd "$( dirname "$0" )" && pwd )"

function main {
  export ANSIBLE_PYTHON_VERSION="2.7.17"

  export AWS_REGION="eu-west-1"
  export AWS_DEFAULT_REGION="$AWS_REGION"

  cd $repo

  setup_node_version
  setup_python_for_ansible

  discord_alarm_webhook_secret_arn="$(aws secretsmanager describe-secret --secret-id discord-alarm-webhook --query ARN --output text)"

  ANSIBLE_CONFIG="$repo/ansible/ansible.cfg" \
  ANSIBLE_LIBRARY="$repo/ansible/library" \
  ansible-playbook \
    --vault-password-file=./get_vault_password.sh \
    --extra-vars=@ansible/secrets.yml \
    --extra-vars "discord_alarm_webhook_secret_arn=$discord_alarm_webhook_secret_arn" \
    ansible/deploy.yml
}

function setup_node_version {
  pushd "$repo"
  set +o errexit +o nounset
  export NVM_DIR="$repo/.nvm"
  source "$repo/web/nvm.sh"
  nvm install
  set -o errexit -o nounset
  popd
}

function setup_python_for_ansible {
  pushd "$repo/ansible"
  eval "$(pyenv init -)"
  pyenv install --skip-existing "$ANSIBLE_PYTHON_VERSION"
  pyenv local "$ANSIBLE_PYTHON_VERSION"

  python -m pip install pipenv
  python -m pipenv install
  source "$(python -m pipenv --venv)/bin/activate"
  popd
}

main
