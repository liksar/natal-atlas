# Implementation notes

- `Client` contains private identity/notes. `Chart` holds the stable random token,
  public display name and current revision. `ChartRevision` stores immutable
  birth input, resolved time, full-precision result and version/fingerprint metadata.
- `save_chart` calculates first, then acquires a PostgreSQL row lock in a short
  transaction and checks the submitted revision. Submission keys prevent duplicate
  creation/repeated writes. No raw Django ModelAdmin edits bypass this service.
- The custom `/admin/clients/` workflow uses Django authentication, permissions,
  CSRF and sessions. Django Admin remains available for users/groups. Client
  ModelAdmin entries are read-only links to the workflow.
- Public view serialization explicitly selects display fields. It never serializes
  Client, actor IDs, internal notes, audit entries or secret authentication state.
- One sync worker thread per process in Gunicorn. A process lock serializes all
  Swiss Ephemeris operations, also protecting development-server calls. No Redis,
  Celery, React, external AI, analytics or CDN are used.
- The pinned tzdata package is forced via an empty system TZPATH so the stored
  tzdata version is the one actually used. Dates are Gregorian; supported birth
  range is 1900–2100. Historical civil-time warnings are retained.
- Geocentric apparent tropical longitudes, speeds, true north node, Placidus with
  explicit Whole Sign fallback. No silent Moshier/JPL source fallback is accepted.
  `pysweph` has three return items for calc_ut and C-style house-cusp indexing;
  both differences are covered by real integration tests.
- House membership is calculated from zodiacal longitude between adjacent cusps,
  inclusive start/exclusive end. Display rounding can advance to the next sign;
  calculation data and house/aspect calculations retain the unrounded longitude.
- Approximate-time margins are elapsed minutes about the resolved UTC instant.
  We sample every minute across the whole interval, store observed signs/houses,
  angle ranges and variable aspects, and mark continuity as unproven. This is an
  uncertainty display, not rectification or a numerical probability distribution.
- Texts are original component explanations, assembled locally from planet, sign,
  house and aspect passages. Their general nature is visible. Persisted text
  version identifies the current corpus; versioned historical text bundles must be
  retained before changing it. Recalculation creates a new revision deliberately.
- Rate limits use transactional PostgreSQL buckets shared by all workers. Forwarded
  IPs are accepted only from configured exact proxy addresses; Caddy replaces the
  header with the actual remote address. Maintenance removes expired sessions and
  inactive limiter buckets; durable submission keys remain.
- `data/` is ignored, versioned by manifests and included in encrypted operational
  backups. Initial download is allowed; user requests never download data.

## Known design limits

The global cities500 dataset is broad but excludes some villages. Region names come from the pinned GeoNames administrative dictionary; country
selectors are localized. Approximate-time alternatives are available in a separate
expandable summary alongside the central chart and warning.
Public chart rendering uses its stored localized presentation snapshot, not the
current interpretation corpus. Language changes create a new revision. There is no independent
historical civil-time guarantee before 1970.

Search values use explicit Unicode NFKC + casefold normalization, including names,
place aliases and revision birthplace metadata. PostgreSQL trigram indexes use
these normalized fields directly so Cyrillic search does not depend on host locale.
