#!/usr/bin/env bash
#
# Set a known password for the FA users of the container database.
# FrontAccounting stores md5($password) in the <prefix>users table.
#
#   scripts/set-dev-password.sh [password] [company-index]
#
set -euo pipefail

cd "$(dirname "$0")/.."

PW="${1:-devpass123}"
COY="${2:-2}"

# shellcheck disable=SC1091
set -a; . ./.env; set +a

DB_NAME="${DB_NAME:-frontacc}"
DB_USER="${DB_USER:-frontacc}"
DB_PASSWORD="${DB_PASSWORD:-}"
# table prefix of the company, e.g. 4_ for company index 2
PREFIX="$(printf '%s' "${FA_COMPANIES}" | tr ';' '\n' | awk -F'|' -v c="$COY" '$1==c {print $3}')"

if [ -z "$PREFIX" ]; then
	echo "could not find a table prefix for company index $COY in FA_COMPANIES" >&2
	exit 1
fi

echo "==> setting password '$PW' for all users of company $COY (prefix $PREFIX)"
docker compose exec -T db mariadb -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
	-e "UPDATE ${PREFIX}users SET password = MD5('$PW'); SELECT id, user_id, real_name FROM ${PREFIX}users;"

echo "==> done, log in with any of those user ids and the password '$PW'"
