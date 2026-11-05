# Temporary Alpha 1 sharing

The application checkpoint is Git tag `alpha-1` (version 0.1.0a1). This separate
hosting adapter runs on Windows with Waitress (one application thread), WhiteNoise,
DEBUG=false and a dedicated PostgreSQL database. Linux production remains the
Gunicorn/Caddy/Compose deployment described elsewhere.

Cloudflare Quick Tunnel maps a temporary HTTPS hostname to **127.0.0.1:8001**.
It does not expose the development server on port 8000 or its SQLite database.
Only fictional demo cards are initially seeded. There is a separate administrator
account; do not reuse the local development password. The source archive is
downloadable at `/source/` under AGPL; it excludes secrets and client data.

Local configuration, credentials and example links are in ignored files:
`.tools/alpha1.json`, `.tools/alpha1-links.json`. No secrets belong in this document.
The configured hostname must match the running tunnel exactly. Restarting a Quick
Tunnel assigns another hostname, so update configuration and restart the alpha
application. Its old public URLs will stop working; saved chart tokens remain in
the isolated alpha database.

Before starting, run `python ops/alpha.py prepare` with the project virtualenv.
Then keep `python ops/alpha.py serve`, PostgreSQL and `cloudflared tunnel --url
http://127.0.0.1:8001 --protocol http2` running. A source archive corresponding to
the deployed commit must exist at `.tools/natal-atlas-alpha-1-source.zip`.

This is for small feedback sessions, not continuous production. The PC must remain
awake and connected. Quick Tunnels have no uptime guarantee and their hostname
changes on restart: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/.
Use fictional data during evaluation; plan domain, offsite backup and Linux native
architecture validation before service to actual clients.
