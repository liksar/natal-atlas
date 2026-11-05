# Alpha 1 — 2026-11-05

Version: 0.1.0a1. Git tag: alpha-1.

Frozen first testable release: real Swiss Ephemeris calculations; administrator
client workflow; stable secret links; fixed EN/UK/RU client-language snapshots;
independent administrative language; exact/approximate/unknown birth time;
worldwide local place search and manual coordinates.

Local browser create/edit/open workflow verified. Current automated suite: 38
backend tests, 37 passing and one PostgreSQL-only concurrency test skipped in
the SQLite preview; 3 frontend regression tests passing. Earlier PostgreSQL
checks and recovery rehearsal are recorded in docs/VALIDATION.md.

Source snapshot excludes local databases, credentials, backups and raw data
bundles. Public alpha hosting is configured separately from this checkpoint.
Production Linux/container/arm64 verification and encrypted server backup tests
remain release gates. See docs/VALIDATION.md for details.
