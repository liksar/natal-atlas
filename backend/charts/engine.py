"""Swiss Ephemeris access. Production: sync workers, one thread per process."""
import hashlib
import json
import math
import os
import threading
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path
import swisseph as swe
from .timeutils import resolve_time

RULES = json.loads(Path(__file__).with_name('rules.json').read_text())
RULES_VERSION = RULES['version']
TEXT_VERSION = '1.0.0'
BODIES = [('sun', swe.SUN), ('moon', swe.MOON), ('mercury', swe.MERCURY), ('venus', swe.VENUS), ('mars', swe.MARS), ('jupiter', swe.JUPITER), ('saturn', swe.SATURN), ('uranus', swe.URANUS), ('neptune', swe.NEPTUNE), ('pluto', swe.PLUTO), ('node', swe.TRUE_NODE)]
ASPECTS = RULES['aspects']
LOCK = threading.Lock()

class CalculationError(ValueError):
    pass

def verify_files(path):
    path = Path(path)
    manifest = path / 'manifest.json'
    if not manifest.exists():
        raise CalculationError('Ephemeris manifest missing. Run ops/setup_data.py first.')
    info = json.loads(manifest.read_text())
    required = {'sepl_18.se1', 'semo_18.se1'}
    if not required.issubset(info['files']):
        raise CalculationError('Incomplete ephemeris manifest.')
    for name, digest in info['files'].items():
        file = path / name
        if file.parent.resolve() != path.resolve() or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise CalculationError('Ephemeris checksum mismatch or missing file.')
    return hashlib.sha256(manifest.read_bytes()).hexdigest()

def separation(a, b):
    return abs((a - b + 180) % 360 - 180)

def house_of(lon, cusps):
    for i, start in enumerate(cusps):
        end = cusps[(i + 1) % 12]
        if (lon - start) % 360 < (end - start) % 360:
            return i + 1
    raise CalculationError('Invalid house boundaries.')

def positions(utc, lat, lon, houses=True):
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60 + utc.second/3600)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    planets = []
    for key, body in BODIES:
        try:
            values, actual, error = swe.calc_ut(jd, body, flags)
        except swe.Error as exc:
            raise CalculationError('The ephemeris could not calculate this chart.') from exc
        if error.strip():
            raise CalculationError('Swiss Ephemeris reported a calculation warning; the result was not saved.')
        if not actual & swe.FLG_SWIEPH or actual & (swe.FLG_MOSEPH | swe.FLG_JPLEPH):
            raise CalculationError('Requested Swiss ephemeris unavailable; fallback rejected.')
        planets.append({'key': key, 'longitude': values[0] % 360, 'speed': values[3], 'retrograde': values[3] < 0, 'sign': int(values[0] % 360 // 30)})
    result = {'planets': planets, 'cusps': [], 'angles': {}, 'house_system': None, 'warnings': []}
    if houses:
        try:
            cusps, angles = swe.houses_ex(jd, lat, lon, RULES['house_system'].encode(), 0)
            system = 'Placidus'
        except swe.Error:
            try:
                cusps, angles = swe.houses_ex(jd, lat, lon, RULES['polar_fallback'].encode(), 0)
            except swe.Error as exc:
                raise CalculationError('Houses cannot be calculated for these coordinates and time.') from exc
            system = 'Whole Sign'
            result['warnings'].append('polar_fallback')
        # pysweph >=2.10.3.4 follows C indexing: element zero is unused.
        cusps = cusps[1:13]
        if not all(math.isfinite(x) for x in (*cusps, *angles)):
            raise CalculationError('Non-finite house result.')
        result.update(cusps=list(cusps), angles={'asc': angles[0], 'mc': angles[1]}, house_system=system)
        for p in planets:
            p['house'] = house_of(p['longitude'], cusps)
    result['aspects'] = []
    for i, a in enumerate(planets[:RULES['aspect_body_count']]):
        for b in planets[i+1:RULES['aspect_body_count']]:
            if not houses and 'moon' in (a['key'], b['key']):
                continue
            for name, angle, orb in ASPECTS:
                delta = abs(separation(a['longitude'], b['longitude']) - angle)
                if delta <= orb:
                    result['aspects'].append({'a': a['key'], 'b': b['key'], 'type': name, 'orb': delta})
    return result

def calculate(data, ephemeris_path):
    fingerprint = verify_files(ephemeris_path)
    mode = data['time_mode']
    if mode not in ('exact','approximate','unknown'):
        raise CalculationError('Invalid time mode.')
    utc, offset, source = resolve_time(data['date'], RULES['unknown_local_time'] if mode == 'unknown' else data['time'], data['timezone'], data.get('fold'), data.get('manual_offset'), data.get('offset_reason', ''))
    if not 1900 <= int(data['date'][:4]) <= 2100:
        raise CalculationError('Supported birth years: 1900–2100.')
    lat, lon = float(data['latitude']), float(data['longitude'])
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise CalculationError('Invalid coordinates.')
    with LOCK:
        # The C library uses narrow Windows paths. A relative path avoids the
        # non-ASCII workspace prefix without copying any data outside the project.
        library_path = os.path.relpath(ephemeris_path) if os.name == 'nt' else str(ephemeris_path)
        swe.set_ephe_path(library_path)
        swe.set_topo(0, 0, 0)
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
        swe.set_delta_t_userdef(swe.DELTAT_AUTOMATIC)
        swe.set_tid_acc(swe.TIDAL_AUTOMATIC)
        result = positions(utc, lat, lon, mode != 'unknown')
        if mode == 'approximate':
            margin = int(data.get('uncertainty_minutes', 0))
            if not 1 <= margin <= 720:
                raise CalculationError('Approximate time needs an uncertainty of 1–720 minutes.')
            # Every minute in the interval; never label unsampled continuity as proven.
            samples = [positions(utc + timedelta(minutes=n), lat, lon) for n in range(-margin, margin+1)]
            aspect_sets = [{(a['a'], a['b'], a['type']) for a in r['aspects']} for r in samples]
            union = set.union(*aspect_sets)
            common = set.intersection(*aspect_sets)
            result['uncertainty'] = {'minutes': margin, 'sample_step_seconds': 60, 'continuity_guaranteed': False, 'utc_start': (utc-timedelta(minutes=margin)).isoformat(), 'utc_end': (utc+timedelta(minutes=margin)).isoformat(), 'house_systems': sorted({r['house_system'] for r in samples}), 'angles': {key: {'sampled_signs': sorted({int(r['angles'][key] // 30) for r in samples}), 'min_delta_degrees': min((r['angles'][key]-result['angles'][key]+180)%360-180 for r in samples), 'max_delta_degrees': max((r['angles'][key]-result['angles'][key]+180)%360-180 for r in samples)} for key in ('asc','mc')}, 'variable_aspects': [list(a) for a in sorted(union-common)], 'planets': {p['key']: {'signs': sorted({r['planets'][i]['sign'] for r in samples}), 'houses': sorted({r['planets'][i].get('house') for r in samples})} for i, p in enumerate(result['planets'])}}
            result['warnings'].append('approximate_time')
    if int(data['date'][:4]) < 1970:
        result['warnings'].append('historical_time')
    if mode == 'unknown':
        result['warnings'].append('unknown_time')
    result.update(schema_version=1, rules_version=RULES_VERSION, text_version=TEXT_VERSION, engine=swe.version, wrapper=version('pysweph'), tzdata=version('tzdata'), ephemeris=fingerprint, utc=utc.isoformat(), utc_offset=offset, utc_offset_seconds=round(offset*60), offset_source=source, time_mode=mode)
    return result
