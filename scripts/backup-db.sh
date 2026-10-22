#!/usr/bin/env bash
#
# Dump the container database to a file.
#
#   scripts/backup-db.sh [output.sql]
#
set -euo pipefail

cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
set -a; . ./.env; set +a

OUT="${1:-backups/frontacc-$(date +%Y%m%d-%H%M%S).sql}"
mkdir -p "$(dirname "$OUT")"

DB_NAME="${DB_NAME:-frontacc}"
DB_USER="${DB_USER:-frontacc}"
DB_PASSWORD="${DB_PASSWORD:-}"

echo "==> dumping '$DB_NAME' to $OUT"
docker compose exec -T db mariadb-dump \
	--single-transaction \
	--quick \
	--routines \
	--triggers \
	--events \
	--default-character-set=utf8mb4 \
	-u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$OUT"

echo "==> $(du -h "$OUT" | cut -f1) written to $OUT"
