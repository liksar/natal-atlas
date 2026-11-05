"""Version-one local text assembly. Stored snapshots are never rebuilt on reads."""
from types import SimpleNamespace
from .engine import ASPECTS
from .i18n import WORDS, PLANETS, SIGNS, ASPECT_NAMES, context
from .texts import interpretation, house_text, aspect_text

def build_presentation_v1(result, lang):
    seconds = round(result['utc_offset'] * 60)
    sign = '+' if seconds >= 0 else '−'
    hours, remainder = divmod(abs(seconds),3600)
    minutes, seconds_part = divmod(remainder,60)
    result = {**result,'utc_offset_label':f'{sign}{hours:02}:{minutes:02}'+(f':{seconds_part:02}' if seconds_part else '')}
    rows = []
    for i, p in enumerate(result['planets']):
        # Round first, then derive sign; 29°59.6′ becomes 0° of next sign.
        total = round(p['longitude'] * 60) % 21600
        rows.append({**p, 'name': PLANETS[lang][i], 'sign_name': SIGNS[lang][total // 1800], 'position': f'{total % 1800 // 60}°{total % 60:02d}′', 'text': interpretation(lang, p['key'], p['sign']), 'house_text': house_text(lang, p.get('house'))})
    by_key = {r['key']: r for r in rows}
    aspects = [{**a, 'a_name': by_key[a['a']]['name'], 'b_name': by_key[a['b']]['name'], 'name': ASPECT_NAMES[lang][[x[0] for x in ASPECTS].index(a['type'])], 'text': aspect_text(lang, a['type'])} for a in result['aspects']]
    asc = result['angles'].get('asc')
    uncertainty_rows = []
    variable_aspects = []
    if result.get('uncertainty'):
        for row in rows:
            possibilities = result['uncertainty']['planets'][row['key']]
            uncertainty_rows.append({'name':row['name'],'signs':', '.join(SIGNS[lang][i] for i in possibilities['signs']),'houses':', '.join(str(i) for i in possibilities['houses'])})
        for a,b,kind in result['uncertainty'].get('variable_aspects',[]):
            variable_aspects.append(by_key[a]['name']+' · '+by_key[b]['name']+' · '+ASPECT_NAMES[lang][[x[0] for x in ASPECTS].index(kind)])
    return {'schema_version':1,'lang':lang,'t':context(SimpleNamespace(LANGUAGE_CODE=lang))['t'],'rows':rows,'aspects':aspects,'uncertainty_rows':uncertainty_rows,'variable_aspects':variable_aspects,'warnings':[WORDS[lang].get(w,w) for w in result['warnings']], 'asc_text':interpretation(lang,'asc',int(asc//30)) if asc is not None else '', 'signs':SIGNS[lang]}
