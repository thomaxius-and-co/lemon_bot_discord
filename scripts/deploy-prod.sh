#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail
source "$( dirname "${BASH_SOURCE[0]}" )/common-functions.sh"

function main {
  export ENV="prod"
  setup_aws
  init_node

  cd "$repo"
  npm ci
  npx cdk bootstrap "aws://$AWS_ACCOUNT_ID/$AWS_REGION"
  npx cdk deploy \
    --app "npx ts-node infra/Application.ts" \
    Application
}

main "$@"
