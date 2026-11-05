# Celestial Atlas / Небесний атлас

Local-first natal chart service. Python 3.12, Django 5.2 LTS, PostgreSQL 16,
Swiss Ephemeris, TypeScript/Vite and an interactive SVG wheel. English,
Ukrainian and Russian. AGPL-3.0. No external runtime APIs, client accounts,
payment services or automatic messaging.

**Status:** working local implementation; see [validation and remaining work](docs/VALIDATION.md).
No production deployment has been performed. Original specification:
[docs/ORIGINAL_SPEC_RU.md](docs/ORIGINAL_SPEC_RU.md); agreed changes:
[PROJECT_DECISIONS_UK.md](PROJECT_DECISIONS_UK.md).

## Local Windows preview

The current workspace contains a development Python environment and verified local
data under ignored `.venv/`, `.tools/` and `data/`. From PowerShell:

```powershell
./ops/dev.ps1
```

Open http://127.0.0.1:8000. This development script uses SQLite for a convenient
preview; production uses PostgreSQL. To administer the preview, run
`./ops/manage.ps1 createsuperuser` in another terminal. No administrator password is provided or
stored in the repository. `_demo_author` is inactive and has an unusable password.

For a fresh checkout, install uv and Node 24 from their official sources:

```powershell
uv sync --frozen
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
uv run python ops/setup_data.py
uv run python ops/setup_places.py
$env:DJANGO_DEBUG='true'
$env:LOCAL_SQLITE='1'
# Set a random DJANGO_SECRET_KEY privately before running management commands.
uv run python backend/manage.py migrate
uv run python backend/manage.py import_places --manifest data-manifests/places.json
uv run python backend/manage.py createsuperuser
uv run python backend/manage.py demo
uv run python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

The Windows C ephemeris library requires an ASCII path. Running from the project
root uses the relative `data/ephe` path, even when the workspace name is Cyrillic.

## Workflow

Sign in at `/admin/`; select **Atlas / Clients**. Add a client, choose a city from
the local search or enter coordinates and an IANA timezone manually. A selected
city is resolved again on the server; coordinates from the browser are not trusted.
Choose exact, approximate (±1–720 minutes) or unknown time. The uncertainty margin
is elapsed time around the resolved UTC instant. A repeated local clock time needs
an explicit occurrence selection; a nonexistent time is rejected.

Create a chart, then use **Copy personal link** or **Open chart**. The URL is only
retrieved after this explicit administrator action. Anyone with the URL can view
the public display name and birth data. Internal names and notes are excluded.
The same URL shows a new revision after a successful correction. Failed calculations
leave the old revision intact. Edits require a reason and reject stale versions.
Recalculation without changed birth data is available through the same edit form.

Unknown time uses an explicitly assumed local noon; no houses, ASC, MC or Moon
aspects. Approximate time displays a central chart and samples the interval every
minute; it never claims continuity between samples or exact angles/houses.
Houses use ecliptic-longitude intervals, inclusive cusp start and exclusive end.
This is not a 3D house-position calculation that includes planetary latitude.

## Checks

```text
uv run python backend/manage.py test charts
npm ci --prefix frontend
npm run build --prefix frontend
npm test --prefix frontend
uv lock --check
```

Set database and Django environment variables before management commands.
Tests use real local ephemerides, official `swetest` fixtures and archived NASA
JPL Horizons reference values; no test downloads are needed.

## Production on Linux

Use [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). It documents installation,
license acknowledgement, backups, restoration, migration and launch checks.
Docker is not installed on the current Windows machine; multiarchitecture images
and the Linux recovery scripts remain a release gate.

## Data and licenses

GeoNames CC BY 4.0: https://www.geonames.org/. The global cities500 snapshot
contains small towns and administrative seats, not every village. Missing locations
can be entered manually. Download versions and SHA256 values are in `data-manifests/`.
Because GeoNames publishes rolling archives, a later download can have a different
hash: installation stops instead of silently changing the dataset. Preserve the
verified `data/` directory as an encrypted offline bundle or review and pin a new
dataset deliberately.

All interpretation text is original, local and versioned. Planet, sign, house and
aspect passages are assembled into readable sections. These are transparent general
symbolic explanations, not AI-generated individual predictions.
See [LICENSES.md](LICENSES.md) and [text manifest](data-manifests/texts.json).
Before public launch, provide the Corresponding Source of the deployed release
via `SOURCE_URL`. Keep databases, tokens, backups and `.env` private.

The verified local data bundle can be recreated with `uv run python ops/package_data.py`
and transferred as `natal-atlas-data.tar.gz`; extract it at the repository root and
run the verification/import commands before starting the service.

## Client chart language

The administrator selects English, Ukrainian or Russian in the client form.
That language and the completed localized explanation/label snapshot are stored
in every revision. Client pages have no language selector and ignore browser
language or `?lang=`. Administrator interface language remains independent.
Changing a chart language through the edit form creates a new revision while
preserving its personal URL. Earlier revisions retain their stored explanations.
Existing pre-language charts migrate to Ukrainian; an administrator can change it.
