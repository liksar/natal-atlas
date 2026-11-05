import sys
import tarfile
from pathlib import Path
archive, destination = map(Path, sys.argv[1:])
destination.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive) as tar:
    tar.extractall(destination, filter='data')
