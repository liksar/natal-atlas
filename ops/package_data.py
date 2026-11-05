"""Create a checksum-pinned installation bundle without client data or secrets."""
import hashlib
import json
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
files = [root / 'data/ephe/manifest.json']
ephemeris = json.loads((root/'data-manifests/ephemeris.json').read_text())
for name, info in ephemeris['files'].items():
    path=root/'data/ephe'/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=info['sha256']:
        raise SystemExit('Ephemeris checksum mismatch')
    files.append(path)
places=json.loads((root/'data-manifests/places.json').read_text())
for info in [{'path':places['archive'],'sha256':places['sha256']},*places.get('supplementary',[])]:
    path=root/info['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=info['sha256']:
        raise SystemExit('Place checksum mismatch')
    files.append(path)
output=root/'natal-atlas-data.tar.gz'
with tarfile.open(output,'w:gz') as tar:
    for file in files:
        tar.add(file,arcname=file.relative_to(root).as_posix())
print(f'{output.name}: {output.stat().st_size} bytes; SHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}')
