from django.db import migrations

def freeze_existing(apps, schema_editor):
    from charts.presentation import build_presentation_v1
    Revision = apps.get_model('charts','ChartRevision')
    for revision in Revision.objects.using(schema_editor.connection.alias).all().iterator():
        revision.presentation = build_presentation_v1(revision.result,revision.language)
        revision.save(update_fields=['presentation'])

class Migration(migrations.Migration):
    dependencies=[('charts','0005_chart_language_chartrevision_language_and_more')]
    operations=[migrations.RunPython(freeze_existing,migrations.RunPython.noop)]
