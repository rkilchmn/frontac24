#!/usr/bin/env bash
#
# Manage the credentials of the FrontAccounting test user (Agents.md).
#
#   scripts/agent-credentials.sh show      print the credentials
#   scripts/agent-credentials.sh path      print the file location
#   scripts/agent-credentials.sh env       print them as shell exports
#   scripts/agent-credentials.sh rotate    generate a new password and store it
#
# The file is Agents.md in the project root and is listed in .gitignore.
# Override the location with FA_CREDENTIALS_FILE=/somewhere/else/Agents.md
#
set -euo pipefail

cd "$(dirname "$0")/.."

CRED_FILE="${FA_CREDENTIALS_FILE:-$PWD/Agents.md}"
ACTION="${1:-show}"

# shellcheck disable=SC1091
set -a; . ./.env; set +a
DB_NAME="${DB_NAME:-frontacc}"
DB_USER="${DB_USER:-frontacc}"
DB_PASSWORD="${DB_PASSWORD:-}"

# read a value from the markdown table: | Label | value |
read_value() {
	grep -E "^\|[[:space:]]*$1[[:space:]]*\|" "$CRED_FILE" 2>/dev/null \
		| head -1 | awk -F'|' '{v=$3; gsub(/^[[:space:]]+|[[:space:]]+$/, "", v); print v}'
}

case "$ACTION" in
	path)
		echo "$CRED_FILE"
		;;

	show)
		if [ ! -f "$CRED_FILE" ]; then
			echo "no credentials file at $CRED_FILE" >&2
			echo "create the test user first: make test-user USER=llm_agent COY=2" >&2
			exit 1
		fi
		cat "$CRED_FILE"
		;;

	env)
		if [ ! -f "$CRED_FILE" ]; then
			echo "no credentials file at $CRED_FILE" >&2
			exit 1
		fi
		echo "export FA_URL=\"$(read_value URL)\""
		echo "export FA_USER=\"$(read_value User)\""
		echo "export FA_PASSWORD=\"$(read_value Password)\""
		echo "export FA_COMPANY=\"$(read_value Company)\""
		;;

	rotate)
		if [ ! -f "$CRED_FILE" ]; then
			echo "no credentials file at $CRED_FILE" >&2
			exit 1
		fi
		AGENT_USER="$(read_value User)"
		COY="$(read_value Company)"
		COY="${COY%% *}"          # "2 (FTSS) - ..." -> "2"
		PREFIX="$(printf '%s' "${FA_COMPANIES}" | tr ';' '\n' | awk -F'|' -v c="$COY" '$1==c {print $3}')"
		NEW_PW="$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"

		docker compose exec -T db mariadb -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
			-e "UPDATE ${PREFIX}users SET password = MD5('${NEW_PW}') WHERE user_id = '${AGENT_USER}';" >/dev/null 2>&1

		tmp="$(mktemp)"
		awk -v pw="$NEW_PW" '
			/^\|[[:space:]]*Password[[:space:]]*\|/ {
				n = split($0, a, "|")
				$0 = a[1] "|" a[2] "| " pw " |"
			}
			{ print }
		' "$CRED_FILE" > "$tmp"
		mv "$tmp" "$CRED_FILE"
		chmod 600 "$CRED_FILE"

		echo "password of '$AGENT_USER' rotated, new password stored in $CRED_FILE"
		;;

	*)
		echo "usage: $0 {show|path|env|rotate}" >&2
		exit 1
		;;
esac
