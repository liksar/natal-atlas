"""Fetch a pinned GeoNames snapshot. If upstream changed, stop; never silently repin."""
import hashlib
import json
import urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
manifest = json.loads((ROOT / 'data-manifests/places.json').read_text())
target = ROOT / manifest['archive']
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != manifest['sha256']:
    with urllib.request.urlopen(manifest['source'], timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != manifest['sha256']:
        raise SystemExit('GeoNames rolling download changed. Obtain the pinned offline bundle or review and pin a new manifest before importing.')
    target.write_bytes(data)
for item in manifest.get('supplementary', []):
    file = ROOT / item['path']
    if file.exists() and hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256']:
        continue
    with urllib.request.urlopen(item['source'], timeout=90) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise SystemExit('Supplementary GeoNames snapshot changed; obtain the pinned data bundle.')
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)
print('GeoNames archive and administrative region names verified.')
