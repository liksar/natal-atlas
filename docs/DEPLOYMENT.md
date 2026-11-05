# Linux deployment and recovery

This is the installation contract for this repository. Container commands and
Linux backup scripts have **not yet been executed** on the current Windows host.
Run them on an isolated test server before storing real client data.

## Server

Ubuntu 24.04 LTS; starting point 2 vCPU, 4 GB RAM and 30–50 GB persistent storage.
Install Docker Engine and Compose using https://docs.docker.com/engine/install/ubuntu/.
Use SSH keys, restrict port 22 to your address, expose only 80/443. PostgreSQL and
Gunicorn have no published host ports. Check both provider and operating-system
firewalls. Do not assume UFW protects Docker-published ports.

Keep a stable domain and point its A record to the server. Publish AAAA only with
working IPv6. The fixed private subnet in compose.yaml must not overlap your
existing networks. If changing it, change Caddy's address and TRUSTED_PROXY_IPS
together. Do not expose Gunicorn directly or trust arbitrary forwarding headers.

## Install

Place a reviewed release in `/opt/natal-chart`. Install uv for initial data downloads,
or transfer an already verified offline `data/` bundle from the development machine.
Source releases do not contain client databases or secrets.

```bash
cd /opt/natal-chart
cp .env.example .env
chmod 600 .env
uv sync --frozen
uv run python ops/setup_data.py
uv run python ops/setup_places.py
chmod +x ops/backup.sh ops/restore.sh
```

In `.env`, set DOMAIN, strong random POSTGRES_PASSWORD and DJANGO_SECRET_KEY,
ALLOWED_HOSTS and HTTPS CSRF_TRUSTED_ORIGINS. Set SWISSEPH_LICENSE_MODE=AGPL,
LICENSE_ACKNOWLEDGED=yes, and SOURCE_URL to the downloadable Corresponding Source
of this exact release. Setting an environment flag does not itself fulfill AGPL.
Never include `.env` in published source or support messages.

```bash
docker compose build
docker compose up -d db
docker compose run --rm web python manage.py migrate --noinput
docker compose run --rm web python manage.py import_places --manifest /app/data-manifests/places.json
docker compose run --rm web python manage.py verify_ephemeris
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py check --deploy
docker compose run --rm web python manage.py preflight
docker compose up -d
docker compose ps
```

Reset passwords with `docker compose run --rm web python manage.py changepassword LOGIN`.
Django invalidates older sessions after password changes. No default passwords or
email recovery exist. PostgreSQL initialization requires a nonempty password.
The application refuses production startup without AGPL acknowledgement and a source URL.

Test the full administrator create/search/copy/edit flow and an anonymous private
browser view. Check `/health/ready`, HTTPS, noindex/no-store, no open DB port and
absence of secret URLs in logs. Test restart and recovery of the same URL.
Health responses disclose no versions. Caddy requests are not access-logged;
runtime log request URIs and headers are redacted. Gunicorn request/error logs are
disabled to avoid token leakage; health checks and exit status remain available.

## Encrypted backups

Install `age`, `python3` and `flock` on Ubuntu. Create an age identity on a safe
machine; keep its private file separately from the server. Put only its public
recipient in `/etc/natal-backup.env`:

```text
BACKUP_RECIPIENT=age1YOUR_PUBLIC_RECIPIENT
```

Set this file to mode 600. A backup contains a consistent PostgreSQL custom dump,
version metadata, manifests, release hash, checksums, and the full data bundle.
It excludes `.env`; retain deployment secrets and domain/recovery access separately.

```bash
sudo install -m 644 ops/natal-backup.service /etc/systemd/system/
sudo install -m 644 ops/natal-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now natal-backup.timer
sudo systemctl start natal-backup.service
sudo journalctl -u natal-backup.service
```

Or export BACKUP_RECIPIENT and run `./ops/backup.sh`. The script locks parallel
backup/restore, checks command failures and encrypts before writing the final file.
It retains seven daily and four Sunday copies once those copies have accumulated.
Daily cleanup of sessions and limiter buckets can be scheduled with
`docker compose run --rm web python manage.py cleanup_runtime`.

Copy encrypted files offsite daily using SFTP/scp. A timer creating local files is
not offsite backup. No paid backup provider is required. Check timer failures and
perform a monthly recovery exercise. Aim for 24-hour RPO only with daily offsite
copies; do not claim a four-hour RTO until measured.

## Restore — destructive, requires explicit flag

Start with the matching source release, `.env`, age identity and encrypted backup.
The script checks checksums and the dependency lock before stopping web. It saves
an encrypted pre-restore database, creates an empty replacement database, restores
the dump/data bundle, checks migrations and ephemerides, then starts web. On failure
web stays stopped so that an inconsistent application is not exposed.

```bash
export BACKUP_IDENTITY_FILE=/secure/path/identity.txt
./ops/restore.sh /secure/path/backup.tar.age --confirm-destructive
```

Verify a known personal URL and saved revisions. Keep the same Django secret and
domain; database tokens preserve URLs. Restore is not authorized against a real
production database merely by these examples. Test it on an isolated Compose project
first. Pre-restore data and dumps need their own retention/offsite review.

## Updates and moving servers

Before updating, create and download a backup; retain the current image/release tag.
Test and review migrations, run them as a separate step, then restart services.
Use old images for rollback only if the DB schema is compatible. Otherwise restore
the matching database backup, accounting for newer writes that would be lost.
Never run `docker compose down -v` against retained production data.

For a move, restore and verify on the new host using a local hosts override. Pause
old-server writes, transfer a final backup, change DNS and enable writes on the new
server. Do not allow independent writes to two databases during DNS propagation.

## Oracle Always Free pilot

The same Compose layout is intended for Ubuntu arm64 on an eligible A1 Flex VM.
Validate native arm64 builds and calculation tests first; do not emulate amd64
as the production solution. Check current eligibility, capacity and charges in the
Oracle console before creating resources. Do not automatically upgrade to a paid
account or substitute a paid shape. Independent encrypted backups are essential:
free VM retention and availability are not guaranteed. A paid VPS is preferable
when promising continuing service to real clients. No hosting account was created
or changed by this implementation.
