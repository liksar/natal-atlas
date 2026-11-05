"""Development recovery rehearsal against an already running local PostgreSQL.

Requires PG_BIN, POSTGRES_HOST/PORT/USER/PASSWORD/DB. Creates a new, randomly
named database, restores a pg_dump, compares saved tokens and revisions, then
drops only that newly created test database. Never overwrites the source DB.
"""
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
import psycopg
from psycopg import sql

root = Path(__file__).resolve().parent.parent
source = os.environ['POSTGRES_DB']
target = 'natal_recovery_' + uuid.uuid4().hex[:12]
kwargs = {'host': os.environ['POSTGRES_HOST'], 'port': os.getenv('POSTGRES_PORT','5432'), 'user': os.environ['POSTGRES_USER'], 'password': os.environ['POSTGRES_PASSWORD']}
env = {**os.environ, 'PGPASSWORD': kwargs['password']}
binpath = Path(os.environ['PG_BIN'])
suffix = '.exe' if os.name == 'nt' else ''
artifact = root / '.tools/recovery.dump'
artifact.parent.mkdir(exist_ok=True)
common = ['-h',kwargs['host'],'-p',kwargs['port'],'-U',kwargs['user']]
subprocess.run([str(binpath/('pg_dump'+suffix)),*common,'-Fc','-f',str(artifact),source],env=env,check=True,capture_output=True)
query = 'SELECT c.id::text,c.public_token,c.revision,r.revision,r.input,r.result FROM charts_chart c JOIN charts_chartrevision r ON r.chart_id=c.id ORDER BY c.id,r.revision'
with psycopg.connect(**kwargs, dbname=source) as conn:
    before = conn.execute(query).fetchall()
if not before:
    raise SystemExit('Create at least one synthetic demo chart before rehearsal.')
with psycopg.connect(**kwargs, dbname='postgres', autocommit=True) as admin:
    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(target)))
    try:
        subprocess.run([str(binpath/('pg_restore'+suffix)),*common,'-d',target,'--no-owner','--exit-on-error',str(artifact)],env=env,check=True,capture_output=True)
        with psycopg.connect(**kwargs, dbname=target) as conn:
            after = conn.execute(query).fetchall()
        if before != after:
            raise SystemExit('Recovery mismatch.')
        report = {'source_database':source,'rehearsal':'new temporary PostgreSQL database','chart_revisions_compared':len(before),'public_tokens_identical':True,'inputs_and_results_identical':True,'dump_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'production_shell_scripts_tested':False}
        (root/'docs/recovery-result.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:
        admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(target)))
