"""Operate an isolated, HTTPS-only temporary Windows alpha instance.

Secrets live in ignored .tools/alpha1.json. The tunnel maps only port 8001,
never the development server or local client database on port 8000.
"""
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / '.tools/alpha1.json'

def configure():
    data = json.loads(CONFIG.read_text(encoding='utf-8'))
    os.environ.update({
        'DJANGO_SETTINGS_MODULE':'config.preview', 'DJANGO_DEBUG':'false',
        'LOCAL_SQLITE':'0','LOCAL_PREVIEW_NULL_ORIGIN':'0',
        'DJANGO_SECRET_KEY':data['django_secret'],
        'DJANGO_ALLOWED_HOSTS':data['hostname'],
        'DJANGO_CSRF_TRUSTED_ORIGINS':'https://'+data['hostname'],
        'POSTGRES_HOST':'127.0.0.1','POSTGRES_PORT':'54329',
        'POSTGRES_DB':data['database'],'POSTGRES_USER':data['db_user'],
        'POSTGRES_PASSWORD':data['db_password'],
        'SOURCE_URL':'https://'+data['hostname']+'/source/',
        'SOURCE_ARCHIVE':str(ROOT / '.tools/natal-atlas-alpha-1-source.zip'),
        'APP_RELEASE':'Alpha 1', 'SWISSEPH_LICENSE_MODE':'AGPL',
        'LICENSE_ACKNOWLEDGED':'yes', 'TRUSTED_PROXY_IPS':'',
        'RATE_LIMIT_PUBLIC':'300', 'RATE_LIMIT_LOGIN':'12',
    })
    sys.path.insert(0,str(ROOT/'backend'))
    os.chdir(ROOT)
    return data

def main():
    data=configure()
    import django
    django.setup()
    from django.core.management import call_command
    action=sys.argv[1] if len(sys.argv)>1 else 'serve'
    if action=='prepare':
        call_command('migrate',interactive=False)
        call_command('import_places',manifest=str(ROOT/'data-manifests/places.json'))
        call_command('collectstatic',interactive=False,verbosity=0)
        from django.contrib.auth import get_user_model
        from charts.models import Chart
        from charts.forms import ChartForm
        from charts.services import save_chart
        User=get_user_model()
        admin=User.objects.filter(username=data['admin_username']).first()
        if admin is None:
            admin=User.objects.create_superuser(data['admin_username'],'',data['admin_password'])
        examples=[]
        for lang in ('uk','en','ru'):
            name={'uk':'Софія · Демо Alpha 1','en':'Sophia · Alpha 1 Demo','ru':'София · Демо Alpha 1'}[lang]
            chart=Chart.objects.filter(display_name=name).first()
            if chart is None:
                form=ChartForm({'key':uuid.uuid4(),'revision':0,'internal_name':f'Alpha 1 fictional demo ({lang})','display_name':name,'language':lang,'date':'1995-05-17','time':'14:30','time_mode':'exact','place':'Kyiv, Ukraine','country':'UA','latitude':50.4501,'longitude':30.5234,'timezone':'Europe/Kyiv','reason':'Fictional example for public alpha testing','allow_duplicate':True})
                if not form.is_valid():
                    raise RuntimeError(str(form.errors))
                chart=save_chart(form,admin)
            examples.append({'language':lang,'url':'https://'+data['hostname']+f'/c/{chart.public_token}/'})
        (ROOT/'.tools/alpha1-links.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf-8')
        call_command('preflight')
        print('Isolated public alpha prepared. No local development clients were copied.')
    elif action=='serve':
        call_command('preflight')
        import logging
        logging.getLogger('waitress').addHandler(logging.NullHandler())
        logging.getLogger('waitress').propagate=False
        from django.core.wsgi import get_wsgi_application
        from waitress import serve
        print('Alpha 1 WSGI server on 127.0.0.1:8001 (one calculation thread).',flush=True)
        serve(get_wsgi_application(),host='127.0.0.1',port=8001,threads=1,
              trusted_proxy='127.0.0.1',trusted_proxy_headers={'x-forwarded-proto'},
              clear_untrusted_proxy_headers=True,ident='Alpha 1')
    else:
        raise SystemExit('Usage: alpha.py prepare|serve')

if __name__=='__main__':
    main()
