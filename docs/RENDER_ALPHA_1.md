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

Verification on 2026-11-05: 38 Django tests, 37 passed and one PostgreSQL-only
test skipped with SQLite. Render Docker build succeeded. Hosted commit
`8c07ead` passed readiness (HTTP 200), admin login, Ukrainian language selection,
Cyrillic city lookup, chart calculation and saving, and anonymous public read.
All 236,932 places were imported. Public HTML stays `lang="uk"` with `?lang=ru`,
has no language selector, omits the private note, and returns private/no-store.

Live admin: https://natal-atlas-alpha1.onrender.com/admin/
Fictional demo: https://natal-atlas-alpha1.onrender.com/c/yg-DsJ9d4bNa0a6BxIAOTMikbziqkL6rVjjk27-GpwY/
Existing local clients were not migrated; the hosted database starts separately.
Credentials are stored only in ignored `.tools/render-alpha1-access.json`.
