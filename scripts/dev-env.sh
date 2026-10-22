#!/usr/bin/env bash
#
# Create/refresh .env for the local stack.
# Keeps the existing values, only fills in what is missing and refreshes the
# host uid/gid used by the PHP pool.
#
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
	cp .env.example .env
	echo "created .env from .env.example"
fi

# .env holds the database credentials - keep it readable by you only
chmod 0600 .env

# host uid/gid so that files written by PHP stay owned by you
uid="$(id -u)"
gid="$(id -g)"

set_env() {
	local key="$1" value="$2"
	if grep -qE "^${key}=" .env; then
		sed -i "s|^${key}=.*|${key}=${value}|" .env
	else
		printf '%s=%s\n' "$key" "$value" >> .env
	fi
}

set_env FA_POOL_USER "$uid"
set_env FA_POOL_GROUP "$gid"

# random passwords for a fresh install
if grep -qE "^DB_PASSWORD=change_me$" .env; then
	set_env DB_PASSWORD "$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"
	echo "generated a random DB_PASSWORD"
fi
if grep -qE "^DB_ROOT_PASSWORD=change_me_too$" .env; then
	set_env DB_ROOT_PASSWORD "$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"
	echo "generated a random DB_ROOT_PASSWORD"
fi

# keep the original (non container) database config safe, outside of the
# FrontAccounting source tree
mkdir -p docker/generated
if [ -f core/config_db.php ] && [ ! -f docker/generated/config_db.php.orig ]; then
	cp -p core/config_db.php docker/generated/config_db.php.orig
	echo "kept the original core/config_db.php as docker/generated/config_db.php.orig"
fi

# the container writes the real config_db.php, this is only the placeholder
# that has to exist before docker compose starts (docker would create a
# directory for a missing mount source)
if [ ! -f docker/generated/config_db.php ]; then
	printf '<?php\n// placeholder - overwritten by the container entrypoint\n' > docker/generated/config_db.php
	echo "created docker/generated/config_db.php placeholder"
fi
chmod 0666 docker/generated/config_db.php

echo
echo ".env is ready:"
grep -E '^(HTTP_PORT|DB_NAME|DB_USER|FA_POOL_USER|FA_POOL_GROUP|FA_TIMEZONE|FA_SECURE_ONLY)=' .env | sed 's/^/  /'
echo
echo "next:  make up"
