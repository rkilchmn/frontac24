#!/usr/bin/env bash
#
# Restore the ORIGINAL password hashes from a FrontAccounting dump into the
# container database.
#
#   scripts/restore-prod-passwords.sh [dump.sql.gz]
#
# Use this after scripts/set-dev-password.sh has overwritten the hashes, so
# that the real production passwords work in the container again.
#
set -euo pipefail

cd "$(dirname "$0")/.."

DUMP="${1:-$HOME/frontacc.sql.gz}"
if [ ! -f "$DUMP" ]; then
	echo "dump not found: $DUMP" >&2
	exit 1
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a
DB_NAME="${DB_NAME:-frontacc}"
DB_USER="${DB_USER:-frontacc}"
DB_PASSWORD="${DB_PASSWORD:-}"

WORK="$(mktemp)"
trap 'rm -f "$WORK"' EXIT

case "$DUMP" in
	*.gz) decompress() { gzip -cd "$1"; } ;;
	*)   decompress() { cat "$1"; } ;;
esac

# pull <prefix>,<user_id>,<md5 hash> out of the <prefix>_users inserts
decompress "$DUMP" | python3 -c '
import re, sys
data = sys.stdin.read()
seen = set()
for m in re.finditer(r"INSERT INTO `(\d+)_users` VALUES(.*?);\n", data, re.S):
    prefix, block = m.group(1), m.group(2)
    for row in re.finditer(r"\((\d+),\x27([^\x27]*)\x27,\x27([0-9a-fA-F]{32})\x27,", block):
        uid, login, pwd = row.group(2), row.group(2), row.group(3)
        key = (prefix, row.group(1))
        if key in seen:
            continue
        seen.add(key)
        print("%s\t%s\t%s\t%s" % (prefix, row.group(1), login, pwd))
' > "$WORK"

if [ ! -s "$WORK" ]; then
	echo "no user rows found in $DUMP" >&2
	exit 1
fi

SQL="$(mktemp)"
trap 'rm -f "$WORK" "$SQL"' EXIT
while IFS=$'\t' read -r prefix id login pwd; do
	printf "UPDATE %s_users SET password = '%s' WHERE id = %s;\n" "$prefix" "$pwd" "$id" >> "$SQL"
	printf '  %s_users  id=%s  %s\n' "$prefix" "$id" "$login"
done < "$WORK"

echo "==> applying the original password hashes"
docker compose exec -T db mariadb -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL"

echo "==> done - the original production passwords work again"
