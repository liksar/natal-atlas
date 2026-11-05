"""Installation only: download official ephemerides with pinned checksums."""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    manifest = json.loads((ROOT / 'data-manifests/ephemeris.json').read_text())
    target = ROOT / 'data/ephe'
    target.mkdir(parents=True, exist_ok=True)
    for name, item in manifest['files'].items():
        output = target / name
        if output.exists() and hashlib.sha256(output.read_bytes()).hexdigest() == item['sha256']:
            continue
        with urllib.request.urlopen(item['url'], timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise SystemExit(f'Checksum mismatch: {name}')
        output.write_bytes(data)
    (target / 'manifest.json').write_text(json.dumps({'files': {n: v['sha256'] for n, v in manifest['files'].items()}}))
    print('Official ephemerides verified. No runtime downloads are used.')

if __name__ == '__main__':
    main()
