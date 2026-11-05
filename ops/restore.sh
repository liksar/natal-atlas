#!/usr/bin/env bash
set -euo pipefail
umask 077
if [[ $# != 2 || "$2" != '--confirm-destructive' ]]; then
    echo 'Usage: restore.sh BACKUP.tar.age --confirm-destructive' >&2
    exit 2
fi
: "${BACKUP_IDENTITY_FILE:?Set the age private identity path}"
backup=$(realpath "$1")
cd "$(dirname "$0")/.."
mkdir -p backups
exec 9>backups/.lock
flock -n 9 || { echo 'Backup/restore already running.' >&2; exit 1; }
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
age -d -i "$BACKUP_IDENTITY_FILE" -o "$stage/archive.tar" "$backup"
python3 ops/safe_extract.py "$stage/archive.tar" "$stage/content"
(cd "$stage/content" && sha256sum -c SHA256SUMS >/dev/null)
cmp uv.lock "$stage/content/uv.lock" >/dev/null || { echo 'Use the matching application release before restore.' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == "$(cat "$stage/content/release.txt")" ]] || { echo 'Check out the matching source release before restore.' >&2; exit 1; }
docker compose stop web
# Preserve the current database before dropping anything; encrypted separately.
stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$stage/pre-restore.dump"
age -R <(age-keygen -y "$BACKUP_IDENTITY_FILE") -o "backups/pre-restore-$stamp.dump.age" "$stage/pre-restore.dump"
docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$POSTGRES_DB"'
docker compose exec -T db sh -c 'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < "$stage/content/database.dump"
python3 ops/safe_extract.py "$stage/content/data.tar" "$stage/data-restored"
if [[ -d data ]]; then mv -- data "backups/pre-restore-data-$stamp"; fi
mv -- "$stage/data-restored/data" data
docker compose run --rm -T web python manage.py migrate --check
docker compose run --rm -T web python manage.py verify_ephemeris
docker compose up -d web
echo 'Restored. Verify a saved personal URL before reopening administrative writes.'
