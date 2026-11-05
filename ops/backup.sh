#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
: "${BACKUP_RECIPIENT:?Set the age public recipient in the environment}"
command -v age >/dev/null
mkdir -p backups/daily backups/weekly
exec 9>backups/.lock
flock -n 9 || { echo 'Another backup is running.' >&2; exit 1; }
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$stage/database.dump"
cp uv.lock pyproject.toml compose.yaml Caddyfile "$stage/"
cp -R data-manifests "$stage/"
docker compose run --rm -T web python manage.py runtime_manifest > "$stage/versions.json"
git rev-parse HEAD > "$stage/release.txt"
tar -cf "$stage/data.tar" data
(cd "$stage" && sha256sum database.dump data.tar uv.lock versions.json > SHA256SUMS)
output="backups/daily/$stamp.tar.age"
tar -C "$stage" -cf - . | age -r "$BACKUP_RECIPIENT" -o "$output.partial"
mv -- "$output.partial" "$output"
if [[ $(date -u +%u) == 7 ]]; then cp -- "$output" "backups/weekly/$stamp.tar.age"; fi
python3 ops/retention.py
echo "Encrypted backup created: $output"
echo 'Copy it off this server using SFTP/scp; local storage alone is insufficient.'
