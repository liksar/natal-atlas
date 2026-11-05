# Astronomical reference provenance

`swetest_reference.json` contains actual output from official Swiss Ephemeris
v2.10.03 `swetest.c`, compiled locally with Zig cc on Windows. The source Git
object and executable hash are recorded. Four dates span 1900–2100, with all ten
planets plus the true node. Numeric longitudes and longitudinal speeds use a
1e-6-degree (or degree/day) tolerance. This verifies integration with the same
engine; it does **not** independently verify Swiss Ephemeris itself.

Reproduce with the official source tag and matching pinned ephemeris files:

```sh
cc -O2 -o swetest swetest.c swecl.c swedate.c swehel.c swehouse.c swejpl.c swemmoon.c swemplan.c sweph.c swephlib.c -lm
./swetest -edir/path/to/ephe -b1.1.2000 -ut12:00 -p0123456789t -fPls -g, -head
```

`jpl/reference.json` and raw `.txt` responses archive a separate NASA JPL Horizons
implementation comparison for Sun, Venus, Mars and Jupiter on 2000-01-01 12:00 UT.
Observer is the Earth's centre (`500@399`), quantities 31, apparent ecliptic-of-date
longitudes without atmospheric refraction. Target IDs: 10, 299, 499 and 599.
Tolerance is 0.001 degree (3.6 arcseconds), permitting different time/nutation
models. Observed differences in these samples are much smaller. Both systems
use related JPL underlying ephemeris families, so this is a separate implementation
cross-check, not independent experimental verification of the planetary theory.

Source descriptions: https://ssd.jpl.nasa.gov/horizons/manual.html#obsquan
and https://ssd-api.jpl.nasa.gov/doc/horizons.html.
References were fetched during development only. Some additional requests returned
HTTP 503; no unverified values were substituted. Tests and all customer scenarios
remain completely offline. These samples do not validate every historical civil
timezone or every date in the supported range.
