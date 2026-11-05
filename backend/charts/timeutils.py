from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, reset_tzpath

# Always use the locked tzdata wheel, not an unversioned host database.
reset_tzpath(())

class TimeError(ValueError):
    pass

def resolve_time(day, clock, zone, fold=None, manual_offset=None, comment=''):
    naive = datetime.fromisoformat(f'{day}T{clock}')
    if manual_offset is not None:
        if not -840 <= manual_offset <= 840 or not comment.strip():
            raise TimeError('Manual UTC offset requires ±840 minutes and a reason.')
        return (naive - timedelta(minutes=manual_offset)).replace(tzinfo=timezone.utc), manual_offset, 'manual'
    try:
        tz = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise TimeError('Select a valid IANA time zone.')
    options = {}
    for value in (0, 1):
        aware = naive.replace(tzinfo=tz, fold=value)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None) == naive:
            options[value] = (utc, aware.utcoffset().total_seconds() / 60)
    if not options:
        raise TimeError('This local time does not exist because of a clock change.')
    if len({v[0] for v in options.values()}) > 1 and fold is None:
        offsets = ', '.join(f'fold={k}: UTC{v[1]/60:+g}' for k, v in options.items())
        raise TimeError(f'Ambiguous local time. Select one: {offsets}')
    selected = options.get(int(fold or 0))
    if selected is None:
        raise TimeError('Invalid time occurrence.')
    return *selected, 'iana'
