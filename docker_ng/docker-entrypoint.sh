#!/bin/bash
set -e
FIRST_RUN_FILENAME="docker_first_run"
RALPH_CONF_DIR="/etc/ralph"
RALPH_LOCAL_DIR="/var/local/ralph"

DB_ENV_VARIABLES=(
    DATABASE_NAME
    DATABASE_USER
    DATABASE_PASSWORD
    DATABASE_HOST
    DATABASE_PORT
    DATABASE_ENGINE
)
# TODO: /etc/ralph/conf.d as variable
DB_CONF_PATH="${RALPH_CONF_DIR}/conf.d/database.conf"
DB_CONF_PATH="/tmp/docker_ng/database.conf"

REDIS_ENV_VARIABLES=(
    REDIS_HOST
    REDIS_PORT
    REDIS_DB
    REDIS_PASSWORD
)
REDIS_CONF_PATH="${RALPH_CONF_DIR}/conf.d/redis.conf"
REDIS_CONF_PATH="/tmp/docker_ng/redis.conf"

function push_env_vars_to_config() {
    local conf_path=$1
    shift
    local env_variables=("$@")
    for env_var in "${env_variables[@]}"
    do
        if [[ ! -z "${!env_var}" ]]; then
            sed -ri "s/(${env_var} ?= ?).*/\1${!env_var}/" ${conf_path}
        fi
    done
}

push_env_vars_to_config "$DB_CONF_PATH" "${DB_ENV_VARIABLES[@]}"
push_env_vars_to_config "$REDIS_CONF_PATH" "${REDIS_ENV_VARIABLES[@]}"

