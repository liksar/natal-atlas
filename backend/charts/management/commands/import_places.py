import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from charts.models import City
from charts.search import normalize

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--manifest', required=True)
    def handle(self, *args, **options):
        manifest = json.loads(Path(options['manifest']).read_text())
        if manifest['license'] != 'CC-BY-4.0':
            raise CommandError('Review dataset license before import.')
        archive = settings.ROOT / manifest['archive']
        if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['sha256']:
            raise CommandError('Place archive missing or checksum mismatch. Run ops/setup_places.py.')
        regions = {}
        for item in manifest.get('supplementary', []):
            file = settings.ROOT / item['path']
            if not file.exists() or hashlib.sha256(file.read_bytes()).hexdigest() != item['sha256']:
                raise CommandError('Administrative region file is missing or has changed.')
            for row in csv.reader(file.read_text(encoding='utf-8').splitlines(), delimiter='\t'):
                if len(row) >= 2:
                    regions[row[0]] = row[1]
        count = 0
        batch = []
        with zipfile.ZipFile(archive) as zipped, zipped.open(manifest['member']) as stream:
            for row in csv.reader(io.TextIOWrapper(stream, encoding='utf-8'), delimiter='\t'):
                if len(row) < 19 or not row[17]:
                    continue
                batch.append(City(source_id=row[0], name=row[1], aliases=row[2]+','+row[3], search_text=normalize(','.join(row[1:4])), latitude=float(row[4]), longitude=float(row[5]), country=row[8], region=regions.get(row[8]+'.'+row[10],row[10]), timezone_id=row[17], dataset_version=manifest['dataset_version']))
                if len(batch) >= 2000:
                    self.flush(batch)
                    count += len(batch)
                    batch.clear()
            if batch:
                self.flush(batch)
                count += len(batch)
        self.stdout.write(f'Imported/updated {count} places; source: GeoNames CC BY 4.0.')
    def flush(self, batch):
        City.objects.bulk_create(batch, update_conflicts=True, unique_fields=['source_id'], update_fields=['name','aliases','search_text','latitude','longitude','country','region','timezone_id','dataset_version'])
