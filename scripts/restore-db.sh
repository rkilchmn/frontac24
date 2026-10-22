#!/usr/bin/env bash
#
# Import a mysqldump into the container database.
#
#   scripts/restore-db.sh /path/to/dump.sql
#
# The dump is expected to contain the FA tables of all companies
# (prefixes 0_, 2_, 4_, 6_) - they all live in the same database.
#
set -euo pipefail

cd "$(dirname "$0")/.."

DUMP="${1:-}"
if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
	echo "usage: $0 <dump.sql>" >&2
	exit 1
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a

DB_NAME="${DB_NAME:-frontacc}"
DB_USER="${DB_USER:-frontacc}"
DB_PASSWORD="${DB_PASSWORD:-}"

if ! docker compose ps --status running --services | grep -qx db; then
	echo "the db container is not running - start it with: make up" >&2
	exit 1
fi

echo "==> restoring $(basename "$DUMP") into database '$DB_NAME' ($(du -h "$DUMP" | cut -f1))"

# FrontAccounting writes "SET NAMES latin1;" into its own backup files even
# when the tables are utf8mb3 - importing that as-is would encode the utf8
# bytes twice. Replace it with the charset the data really is.
WORK="$(mktemp)"
trap 'rm -f "$WORK"' EXIT

# plain dump or gzip compressed dump
case "$DUMP" in
	*.gz) decompress() { gzip -cd "$1"; } ;;
	*)   decompress() { cat "$1"; } ;;
esac

if decompress "$DUMP" | grep -qiE '^[[:space:]]*SET NAMES '; then
	decompress "$DUMP" | grep -iE '^[[:space:]]*SET NAMES ' | sed 's/^/    /' >&2
	decompress "$DUMP" | sed -E 's/^([[:space:]]*)SET NAMES [^;]+;/\1SET NAMES utf8mb4;/I' > "$WORK"
	echo "==> replaced the SET NAMES statement with utf8mb4"
else
	decompress "$DUMP" > "$WORK"
fi

# sql_mode is relaxed for the import: FA databases are full of '0000-00-00'
# dates which strict modes reject.
docker compose exec -T db mariadb \
	--default-character-set=utf8mb4 \
	--init-command="SET SESSION sql_mode=''" \
	-u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$WORK"

echo "==> done, tables in the database:"
docker compose exec -T db mariadb -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
	-e "SELECT table_name AS tbl, table_rows AS rowcount FROM information_schema.tables WHERE table_schema='$DB_NAME' ORDER BY table_name;" \
	| head -60
