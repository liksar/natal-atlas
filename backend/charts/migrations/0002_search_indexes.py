from django.db import migrations

def install(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    for table, column in [('charts_city','name'),('charts_city','aliases'),('charts_client','internal_name'),('charts_chart','display_name')]:
        schema_editor.execute(f'CREATE INDEX IF NOT EXISTS {table}_{column}_trgm ON {table} USING gin (UPPER({column}) gin_trgm_ops)')
    schema_editor.execute("CREATE INDEX IF NOT EXISTS chart_place_trgm ON charts_chartrevision USING gin (UPPER(input->>'place') gin_trgm_ops)")
    schema_editor.execute("CREATE INDEX IF NOT EXISTS chart_birth_date ON charts_chartrevision ((input->>'date'))")

class Migration(migrations.Migration):
    dependencies = [('charts','0001_initial')]
    operations = [migrations.RunPython(install, migrations.RunPython.noop)]
