from pathlib import Path
root = Path(__file__).resolve().parent.parent / 'backups'
for name, keep in [('daily', 7), ('weekly', 4)]:
    folder = (root / name).resolve()
    for file in sorted(folder.glob('*.tar.age'), reverse=True)[keep:]:
        if file.resolve().parent != folder:
            raise SystemExit('Unexpected backup path')
        file.unlink()
