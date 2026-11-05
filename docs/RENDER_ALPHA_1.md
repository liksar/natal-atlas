# Render Alpha 1

Source: https://github.com/liksar/natal-atlas (branch `codex/alpha-1`).
`render.yaml` explicitly selects free web and PostgreSQL 16 in Frankfurt.
The free database expires after 30 days; export test data before expiry.
The web service sleeps after inactivity and can take about a minute to wake.

`ops/Render.Dockerfile` bundles checksum-pinned Swiss Ephemeris and GeoNames
files, builds the frontend, and serves static files with WhiteNoise.
No local client database or local credentials are included.

Render generates `DJANGO_SECRET_KEY` and `ALPHA_ADMIN_PASSWORD`.
The initial administrator is `alpha_admin`. The password is available only
in the service environment settings; bootstrap does not reset existing users.
Startup serializes migrations and dataset import with a PostgreSQL advisory lock.
Dataset import is transactional. Gunicorn runs one calculation worker/thread.

Free-tier constraints: no persistent filesystem or shell; all client data is in
PostgreSQL. Automatic application deploys are disabled. No paid disk or worker
is provisioned. Back up PostgreSQL before a major update or database expiry.

Local verification: 38 Django tests, 37 passed and one PostgreSQL-only test
skipped with SQLite. Docker build and hosted verification must be checked in
Render before declaring the deployment ready.
