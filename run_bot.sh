#!/usr/bin/env bash
source "$( dirname "${BASH_SOURCE[0]}" )/scripts/common-functions.sh"

function main {
  cd "$repo"
  docker build -f Dockerfile . --tag lemon
  source "$repo/secrets"
  docker run -it \
    --network host \
    --env DATABASE_HOST=localhost \
    --env DATABASE_PORT=5432 \
    --env DATABASE_NAME=lemon \
    --env DATABASE_USERNAME=lemon \
    --env DATABASE_PASSWORD=lemon \
    --env LEMONBOT_TOKEN \
    --env ADMIN_USER_IDS \
    --env DISCORD_BOT_ID \
    --env DISCORD_CLIENT_ID \
    --env DISCORD_CLIENT_SECRET \
    --env DISCORD_CALLBACK_URL="http://localhost:8080/login/oauth2/code/discord" \
    --env WOLFRAM_ALPHA_APPID \
    --env OPEN_WEATHER_APPID \
    --env BING_CLIENTID \
    --env BING_SECRET \
    --env OSU_API_KEY \
    --env STEAM_API_KEY \
    --env FACEIT_API_KEY \
    --env WEB_SESSION_SECRET \
    --env WITHINGS_CLIENT_ID \
    --env WITHINGS_CLIENT_SECRET \
    --env WITHINGS_CALLBACK_URL="http://localhost:8080/auth/withings/callback" \
    --env KANSALLISGALLERIA_API_KEY \
    lemon


}

main "$@"
