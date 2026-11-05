# Licenses and attribution

Application source and original interpretation texts: AGPL-3.0 (see LICENSE).
Network users must be offered the Corresponding Source of the deployed version.
Set SOURCE_URL to that exact release before production startup. Never publish
client records, tokens, .env files, keys or backups with source code.

- Swiss Ephemeris: copyright Alois Treindl and Dieter Koch, Astrodienst AG;
  AGPL-3.0 branch of the dual license. Preserve upstream notices.
  https://github.com/aloistr/swisseph
- pysweph: AGPL-3.0; modern Python wrapper. Lockfile pins the actual version.
  https://github.com/sailorfe/pysweph
- GeoNames: Creative Commons Attribution 4.0, https://www.geonames.org/.
  Source: https://download.geonames.org/export/dump/; see data manifest.
  The cities500 dataset includes towns above 500 population or administrative seats,
  not every village or historical settlement. Manual input covers missing entries.
- Noto Serif: SIL Open Font License 1.1. Bundled notice:
  backend/static/fonts/OFL.txt. Source: https://github.com/google/fonts/tree/main/ofl/notoserif
- Django: BSD-3-Clause; Python: PSF; PostgreSQL: PostgreSQL License;
  psycopg: LGPL-3.0; argon2-cffi: MIT; tzdata: Apache-2.0 (IANA data public domain);
  Gunicorn: MIT; TypeScript: Apache-2.0; Vite: MIT; Caddy: Apache-2.0.

Dependency notices are retained in their installed packages. Release packaging must
include the source, lockfiles, build scripts and upstream notices needed by AGPL.
Check the chosen artifacts again if dependencies or license mode change.

- django-countries: MIT; bundled localized country names.
