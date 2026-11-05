# Validation — 5 November 2026

## Executed successfully

- Python 3.12.16 environment; locked Django 5.2.19, pysweph 2.10.3.6,
  PostgreSQL 16.15 development server, tzdata 2026.6.
- **29 backend tests passed on real PostgreSQL 16**, including concurrent edit
  conflict protection. SQLite also exercised; its PostgreSQL row-lock test is
  explicitly skipped. Both are development environments, not the production server.
- **3 frontend regression tests passed**: circular labels across 0°, all eleven
  coincident, and a dense Capricorn group. The original longitude array remains
  untouched. Dense real-date chart checked in-browser: 11 labels, zero intersecting
  label bounding boxes after the fix.
- TypeScript type checking and Vite production build passed. JavaScript bundle is
  about 8.4 kB (3.2 kB gzip), excluding CSS and the local font.
- Django `check --deploy --fail-level WARNING` passed with production settings,
  without silenced warnings. `uv lock --check` passed.
- Official Swiss Ephemeris files verified by SHA256; fallback-source rejection
  tested. Four official swetest reference dates (1900, 1950, 2000, 2100) checked
  across ten planets plus true node and longitudinal speed. A separate JPL Horizons
  cross-check covers Sun, Venus, Mars and Jupiter at J2000; see tests/README.md for
  conventions, tolerances and limits.
- Tests cover DST gaps/folds, manual offsets and date crossing, historical offset
  seconds, zodiac wrap, house boundaries, unknown time, polar fallback and sampled
  uncertainty. They also cover atomic creation/edit, error rollback, no empty
  client, durable idempotency, stable URLs, link rotation/revocation, private-note
  exclusion, XSS escaping, CSRF, rate limits, password-change session invalidation,
  EN/UK/RU rendering, Unicode-normalized case-independent search, and authenticated create/edit/search/link requests.
- GeoNames global cities500 archive imported idempotently: **236,932 places**.
  Pinned administrative-name supplement added. Local country names are provided
  in all three languages by django-countries.
- Real pg_dump/pg_restore rehearsal into a new empty PostgreSQL database passed.
  Chart tokens, revisions, input and calculated results matched; the isolated
  temporary recovery database was removed afterwards. See recovery-result.json.
- Caddy 2.11.8 adapted and validated Caddyfile successfully. Its warning about an
  apparently redundant X-Forwarded-For override is intentional: the exact client
  address replaces supplied values, matching the backend's trusted-proxy contract.
- Both shell backup/restore scripts passed Bash syntax checks.
- Browser: actual SVG rendering, Ukrainian content, planet selection, keyboard
  activation, decorative-motion switch and approximate-time alternative table
  checked. Screenshots at widths 360, 390, 768 and 1440 are in `docs/qa/`.
  At all four widths document scrollWidth remained within viewport width.
- An offline data-only bundle was created with checksum validation. It contains
  ephemerides and GeoNames data, not client records, credentials or secrets.

## Local measurements

Sequential measurements on this Windows development computer with PostgreSQL:
exact calculation median 4.12 ms / p95 6.03 ms (50 samples); stored chart response
median 6.34 ms / p95 7.78 ms (30 samples). The cold maximum response was 91.89 ms.
See benchmark-result.json. These exclude network/TLS/browser time and do not
establish capacity on the target VPS or performance at concurrent production load.

## Release gates not yet executed

1. Docker/Compose builds and lifecycle on Linux amd64 and arm64. Docker and WSL
   are unavailable here. Native CI jobs are prepared in `.github/workflows/validate.yml`
   but have not run; no repository was published.
2. End-to-end encrypted Linux `backup.sh`/`restore.sh`, systemd timer, retention
   and offsite transfer on an isolated test server. The successful PostgreSQL
   rehearsal does not prove the container/encryption/systemd layers.
3. Real-domain HTTPS issuance, restart/redeploy and server migration. No domain,
   hosting account or production environment was created or changed.
4. Full browser administrator journey on a normal browser, including clipboard
   permissions and login. The embedded preview browser produced a null Origin for
   POST forms, so its CSRF requests were correctly rejected; authentication and
   CRUD were tested through Django's client instead. No CSRF exception was added.
5. Formal accessibility audit, actual OS reduced-motion emulation, manual screen
   reader testing, and a sustained load/security review. Keyboard activation,
   motion disabling and responsive layouts have been checked, not full certification.
6. Publish the Corresponding Source for the exact release, set SOURCE_URL and
   explicitly acknowledge AGPL before production startup. No source publication
   or public service deployment has been authorized by this implementation step.

## Product limits

- cities500 is worldwide but does not contain every settlement; missing locations
  use manual coordinates and an explicit timezone/offset.
- Approximate time is a per-minute sampled interval, not a continuous proof or
  rectification. All sensitive outputs remain marked provisional.
- Interpretation sections are original, expanded component explanations in all
  three languages; they are labelled general rather than a bespoke expert reading.
- Historical civil time before 1970 can be incomplete. Free hosting availability
  and indefinite access are not guaranteed.

## Fixed client language update

36 backend tests executed on local SQLite: 35 passed; the PostgreSQL-only
concurrency test was skipped. Added tests prove that each of EN/UK/RU is fixed
for a chart despite browser cookies, Accept-Language and query parameters;
public pages have no language selector, reads do not regenerate saved text,
and administrator language changes create a new revision with the same URL.
Five tests cover the opted-in loopback-only opaque-Origin preview handling,
including mandatory CSRF tokens and rejection on deployed hosts/production.
Existing cards migrated to Ukrainian with saved explanation snapshots.

## Browser workflow recheck

Verified actual browser form submission end to end: Ukrainian administrator UI,
local Kyiv search, English client chart, client page without language selector or
private-note leakage, then Russian revision with the same personal URL.
Synthetic QA client removed after verification. `/admin/` and authenticated `/`
now lead to the client list; system user/group administration remains available
at `/admin/system/`. Fixed localized countries/notes/default reason and corrupted
punctuation in the client list. 38 tests executed locally: 37 passed, with only
the PostgreSQL concurrency test skipped in the SQLite preview environment.
This supersedes the earlier pending-browser-journey limitation for the local
embedded preview; production/Linux release gates remain.
