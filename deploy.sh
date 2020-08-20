#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

export ANSIBLE_PYTHON_VERSION="2.7.17"

export AWS_REGION="eu-west-1"
export AWS_DEFAULT_REGION="$AWS_REGION"

ROOT="$( cd "$( dirname "$0" )" && pwd )"
cd $ROOT

set +o errexit
export NVM_DIR="$ROOT/.nvm"
source "$ROOT/web/nvm.sh"
set -o errexit
nvm install

pushd "$ROOT/ansible"
eval "$(pyenv init -)"
pyenv install --skip-existing "$ANSIBLE_PYTHON_VERSION"
pyenv local "$ANSIBLE_PYTHON_VERSION"

python -m pip install pipenv
python -m pipenv install
source "$(python -m pipenv --venv)/bin/activate"
popd

discord_alarm_webhook_secret_arn="$(aws secretsmanager describe-secret --secret-id discord-alarm-webhook --query ARN --output text)"

ANSIBLE_CONFIG="$ROOT/ansible/ansible.cfg" \
ANSIBLE_LIBRARY="$ROOT/ansible/library" \
ansible-playbook \
  --vault-password-file=./get_vault_password.sh \
  --extra-vars=@ansible/secrets.yml \
  --extra-vars "discord_alarm_webhook_secret_arn=$discord_alarm_webhook_secret_arn" \
  ansible/deploy.yml
