import unicodedata
from django.db import migrations

def normalize(value):
    return unicodedata.normalize('NFKC',value).casefold()

def install(apps,schema_editor):
    alias=schema_editor.connection.alias
    for name,field,source in [('Client','search_name',lambda x:x.internal_name),('Chart','search_name',lambda x:x.display_name),('City','search_text',lambda x:x.name+','+x.aliases),('ChartRevision','place_search',lambda x:x.input.get('place',''))]:
        model=apps.get_model('charts',name)
        batch=[]
        for obj in model.objects.using(alias).all().iterator(chunk_size=1000):
            setattr(obj,field,normalize(source(obj)))
            batch.append(obj)
            if len(batch)==1000:
                model.objects.using(alias).bulk_update(batch,[field]);batch=[]
        if batch:
            model.objects.using(alias).bulk_update(batch,[field])
    if schema_editor.connection.vendor=='postgresql':
        for table,column in [('charts_city','name'),('charts_city','aliases'),('charts_client','internal_name'),('charts_chart','display_name')]:
            schema_editor.execute(f'DROP INDEX IF EXISTS {table}_{column}_trgm')
        schema_editor.execute('DROP INDEX IF EXISTS chart_place_trgm')
        for table,column in [('charts_city','search_text'),('charts_client','search_name'),('charts_chart','search_name'),('charts_chartrevision','place_search')]:
            schema_editor.execute(f'CREATE INDEX IF NOT EXISTS {table}_{column}_trgm ON {table} USING gin ({column} gin_trgm_ops)')

class Migration(migrations.Migration):
    dependencies=[('charts','0003_chart_search_name_city_search_text_and_more')]
    operations=[migrations.RunPython(install,migrations.RunPython.noop)]
