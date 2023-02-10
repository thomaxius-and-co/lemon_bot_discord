#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail
source "$( dirname "${BASH_SOURCE[0]}" )/common-functions.sh"

function main {
  export VERSION_TAG="${VERSION_TAG:-local-$( timestamp )-$( git rev-parse HEAD )}"

  export ENV="prod"
  setup_aws
  init_node

  cd "$repo"
  npm ci
  npx cdk bootstrap "aws://$AWS_ACCOUNT_ID/$AWS_REGION"
  npx cdk deploy \
    --require-approval never \
    --app "npx ts-node infra/Application.ts" \
    ImageRepository

  build_and_upload_container_image "$VERSION_TAG" "lemon"

  npx cdk deploy \
    --require-approval never \
    --app "npx ts-node infra/Application.ts" \
    Application
}

function build_and_upload_container_image {
	local -r tag="$1"
	local -r repository_name="$2"
	local -r repository_uri="$( get_repository_uri "$repository_name" )"

	docker build --tag "${repository_uri}:${tag}" .
	aws ecr get-login-password --region "$AWS_REGION" \
		| docker login --username AWS --password-stdin "$repository_uri"
	docker push "${repository_uri}:${tag}"
}

function get_repository_uri {
	local -r repository_name="$1"
	aws ecr describe-repositories --query "repositories[?repositoryName=='${repository_name}'].repositoryUri | [0]" --output text
}

function timestamp {
  date +"%Y%m%d%H%M%S"
}

main "$@"
