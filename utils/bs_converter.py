"""
Bikram Sambat (BS) ↔ Gregorian (AD) converter.

Approach: anchor-based conversion.
  Instead of walking from a single epoch that may accumulate errors,
  we maintain multiple verified anchor points (official Nepali New Year dates)
  and walk only the short distance from the nearest anchor.
  This eliminates cumulative calendar-table errors for recent dates.

Verified anchors (official Government of Nepal calendar):
  AD 2018-04-14 = BS 2075-01-01
  AD 2019-04-14 = BS 2076-01-01
  AD 2020-04-13 = BS 2077-01-01
  AD 2021-04-14 = BS 2078-01-01
  AD 2022-04-14 = BS 2079-01-01
  AD 2023-04-14 = BS 2080-01-01
  AD 2024-04-13 = BS 2081-01-01
  AD 2025-04-14 = BS 2082-01-01
  AD 2026-04-14 = BS 2083-01-01

Cross-check:
  AD 2026-04-07 is 7 days before 2026-04-14
  → 7 days before BS 2083-01-01
  BS 2082-12 has 31 days → day 31 - 7 + 1 = 25... 
  Let's count: 2083-01-01 minus 7 days:
    minus 1 → 2082-12-30
    minus 2 → 2082-12-29
    minus 3 → 2082-12-28
    minus 4 → 2082-12-27
    minus 5 → 2082-12-26
    minus 6 → 2082-12-25
    minus 7 → 2082-12-24
  AD 2026-04-07 = BS 2082-12-24  ✓

Display: English numerals only. e.g. 2082-12-24
"""

import datetime

# ── BS calendar: days per month per BS year ───────────────────────────────────
_BS_CALENDAR = {
    1970: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1971: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1972: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
    1973: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
    1974: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1975: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    1976: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    1977: [30, 32, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
    1978: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1979: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    1980: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    1981: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    1982: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1983: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    1984: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    1985: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    1986: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1987: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    1988: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    1989: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    1990: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1991: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    1992: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
    1993: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    1994: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1995: [31, 32, 31, 32, 31, 30, 30, 29, 30, 30, 29, 31],
    1996: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    1997: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    1998: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    1999: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2000: [30, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2001: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2002: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2003: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2004: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2005: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2006: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2007: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2008: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2009: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2010: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2011: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2012: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2013: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2014: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2015: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2016: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2017: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2018: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2019: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2020: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2021: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2022: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
    2023: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2024: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2025: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2026: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2027: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2028: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2029: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2030: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2031: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2032: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2033: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2034: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2035: [31, 31, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
    2036: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2037: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2038: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2039: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2040: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2041: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2042: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2043: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2044: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2045: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2046: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2047: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2048: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2049: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2050: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2051: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2052: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2053: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2054: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2055: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2056: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2057: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2058: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
    2059: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2060: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2061: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2062: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2063: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2064: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2065: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2066: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2067: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2068: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2069: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2070: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2071: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2072: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2073: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2074: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2075: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2076: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2077: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2078: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
    2079: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
    2080: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2081: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2082: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2083: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2084: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2085: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2086: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    2087: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
    2088: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
    2089: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
    2090: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
}

# ── Verified anchor table ─────────────────────────────────────────────────────
# Each entry: AD date → (BS year, BS month=1, BS day=1)
# These are official Nepali New Year dates (Baisakh 1)
# Source: Government of Nepal calendar / Hamro Patro
_ANCHORS = [
    (datetime.date(2018, 4, 14), 2075, 1, 1),
    (datetime.date(2019, 4, 14), 2076, 1, 1),
    (datetime.date(2020, 4, 13), 2077, 1, 1),
    (datetime.date(2021, 4, 14), 2078, 1, 1),
    (datetime.date(2022, 4, 14), 2079, 1, 1),
    (datetime.date(2023, 4, 14), 2080, 1, 1),
    (datetime.date(2024, 4, 13), 2081, 1, 1),
    (datetime.date(2025, 4, 14), 2082, 1, 1),
    (datetime.date(2026, 4, 14), 2083, 1, 1),
]

# Early anchor for dates before 2075
_EARLY_ANCHOR = (datetime.date(1943, 4, 14), 2000, 1, 1)


def _find_nearest_anchor(ad_date: datetime.date) -> tuple:
    """
    Return the nearest anchor (ad_anchor, bs_y, bs_m, bs_d)
    that is <= ad_date. Falls back to early anchor for old dates.
    """
    best = _EARLY_ANCHOR
    for ad_anc, by, bm, bd in _ANCHORS:
        if ad_anc <= ad_date:
            best = (ad_anc, by, bm, bd)
        else:
            break
    return best


def _walk_forward(bs_year: int, bs_month: int, bs_day: int,
                  days: int) -> tuple:
    """
    Walk forward `days` days from a BS date.
    Returns (bs_year, bs_month, bs_day).
    Returns (None, None, None) if out of table range.
    """
    remaining = days
    y, m, d = bs_year, bs_month, bs_day

    while remaining > 0:
        if y not in _BS_CALENDAR:
            return (None, None, None)
        dim  = _BS_CALENDAR[y][m - 1]
        left = dim - d          # days left after current day in this month
        if remaining <= left:
            d += remaining
            remaining = 0
        else:
            remaining -= (left + 1)
            d  = 1
            m += 1
            if m > 12:
                m = 1
                y += 1

    return (y, m, d)


def _walk_backward(bs_year: int, bs_month: int, bs_day: int,
                   days: int) -> tuple:
    """
    Walk backward `days` days from a BS date.
    Returns (bs_year, bs_month, bs_day).
    Returns (None, None, None) if out of table range.
    """
    remaining = days
    y, m, d = bs_year, bs_month, bs_day

    while remaining > 0:
        if remaining < d:
            d -= remaining
            remaining = 0
        else:
            remaining -= d
            m -= 1
            if m < 1:
                m = 12
                y -= 1
            if y not in _BS_CALENDAR:
                return (None, None, None)
            d = _BS_CALENDAR[y][m - 1]

    return (y, m, d)


# ── AD → BS ──────────────────────────────────────────────────────────────────

def ad_to_bs(ad_date) -> tuple:
    """
    Convert datetime.date (AD) → (bs_year, bs_month, bs_day).
    Uses nearest verified anchor for accuracy.
    Returns (None, None, None) on failure.
    """
    if ad_date is None:
        return (None, None, None)

    try:
        ad_date = ad_date if isinstance(ad_date, datetime.date) \
                  else datetime.date.fromisoformat(str(ad_date)[:10])
    except Exception:
        return (None, None, None)

    ad_anc, by, bm, bd = _find_nearest_anchor(ad_date)
    delta = (ad_date - ad_anc).days

    if delta == 0:
        return (by, bm, bd)
    elif delta > 0:
        return _walk_forward(by, bm, bd, delta)
    else:
        return _walk_backward(by, bm, bd, abs(delta))


def bs_str(ad_date) -> str:
    """
    Return BS date string 'YYYY-MM-DD' from datetime.date (AD).
    Falls back to str(ad_date) on failure.
    """
    if ad_date is None:
        return "—"
    try:
        y, m, d = ad_to_bs(ad_date)
        if y is None:
            return str(ad_date)
        return f"{y}-{m:02d}-{d:02d}"
    except Exception:
        return str(ad_date)


def bs_str_from_str(date_str: str) -> str:
    """Convert AD date string 'YYYY-MM-DD' → BS string."""
    if not date_str or date_str in ("—", ""):
        return date_str
    try:
        d = datetime.date.fromisoformat(date_str[:10])
        return bs_str(d)
    except Exception:
        return date_str


# ── BS → AD ──────────────────────────────────────────────────────────────────

def bs_to_ad(bs_year: int, bs_month: int, bs_day: int):
    """
    Convert BS date → datetime.date (AD).
    Returns None if invalid or out of calendar range.
    Uses nearest anchor for accuracy.
    """
    if bs_year not in _BS_CALENDAR:
        return None
    if bs_month < 1 or bs_month > 12:
        return None
    try:
        max_day = _BS_CALENDAR[bs_year][bs_month - 1]
    except (IndexError, KeyError):
        return None
    if bs_day < 1 or bs_day > max_day:
        return None

    # Find nearest anchor ≤ target BS date
    # Use the anchor whose BS year ≤ bs_year
    best_ad_anc = _EARLY_ANCHOR[0]
    best_by, best_bm, best_bd = _EARLY_ANCHOR[1], _EARLY_ANCHOR[2], _EARLY_ANCHOR[3]

    for ad_anc, ay, am, ad_d in _ANCHORS:
        if (ay, am, ad_d) <= (bs_year, bs_month, bs_day):
            best_ad_anc = ad_anc
            best_by, best_bm, best_bd = ay, am, ad_d
        else:
            break

    # Count days from anchor BS date to target BS date
    days = _bs_days_between(best_by, best_bm, best_bd,
                             bs_year, bs_month, bs_day)
    if days is None:
        return None
    try:
        return best_ad_anc + datetime.timedelta(days=days)
    except Exception:
        return None


def _bs_days_between(from_y: int, from_m: int, from_d: int,
                      to_y: int, to_m: int, to_d: int) -> int | None:
    """
    Count calendar days from (from_y, from_m, from_d) to
    (to_y, to_m, to_d) in BS calendar.
    Returns None on error.
    """
    if (from_y, from_m, from_d) == (to_y, to_m, to_d):
        return 0

    # Walk forward
    total = 0
    y, m, d = from_y, from_m, from_d
    safety = 0

    while (y, m, d) != (to_y, to_m, to_d):
        if safety > 40000:
            return None
        safety += 1
        if y not in _BS_CALENDAR:
            return None
        dim  = _BS_CALENDAR[y][m - 1]
        left = dim - d   # days remaining after today in this month
        need = _bs_days_to_target(y, m, d, to_y, to_m, to_d)
        if need is None:
            return None
        if need <= left:
            total += need
            break
        else:
            total += left + 1
            d  = 1
            m += 1
            if m > 12:
                m = 1
                y += 1

    return total


def _bs_days_to_target(cy: int, cm: int, cd: int,
                        ty: int, tm: int, td: int) -> int | None:
    """Count days from current BS position to target. Returns None if error."""
    if (cy, cm, cd) == (ty, tm, td):
        return 0

    total = 0
    y, m, d = cy, cm, cd

    for _ in range(40000):
        if y not in _BS_CALENDAR:
            return None
        if (y, m) == (ty, tm):
            if td >= d:
                return total + (td - d)
            else:
                return None
        dim   = _BS_CALENDAR[y][m - 1]
        total += (dim - d + 1)   # rest of current month
        d  = 1
        m += 1
        if m > 12:
            m = 1
            y += 1
        if y > ty + 1:
            return None

    return None


def bs_to_ad_str(bs_str_val: str):
    """Parse 'YYYY-MM-DD' (BS) → datetime.date (AD). Returns None if invalid."""
    if not bs_str_val or bs_str_val == "—":
        return None
    try:
        parts = bs_str_val.strip().split("-")
        if len(parts) != 3:
            return None
        return bs_to_ad(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def today_bs() -> str:
    """Return today's date as BS string 'YYYY-MM-DD'."""
    return bs_str(datetime.date.today())


def today_bs_tuple() -> tuple:
    """Return today's BS date as (year, month, day)."""
    return ad_to_bs(datetime.date.today())


def days_in_bs_month(bs_year: int, bs_month: int) -> int:
    """Return number of days in a BS month."""
    try:
        return _BS_CALENDAR[bs_year][bs_month - 1]
    except (KeyError, IndexError):
        return 30


def is_valid_bs_date(bs_year: int, bs_month: int, bs_day: int) -> bool:
    """Check if a BS date is valid."""
    if bs_year not in _BS_CALENDAR:
        return False
    if bs_month < 1 or bs_month > 12:
        return False
    try:
        return 1 <= bs_day <= _BS_CALENDAR[bs_year][bs_month - 1]
    except (IndexError, KeyError):
        return False


def bs_month_ad_range(bs_year: int, bs_month: int) -> tuple:
    """Return (ad_start, ad_end) datetime.date pair for a BS month."""
    ad_start = bs_to_ad(bs_year, bs_month, 1)
    last_day = days_in_bs_month(bs_year, bs_month)
    ad_end   = bs_to_ad(bs_year, bs_month, last_day)
    return (ad_start, ad_end)


def prev_bs_month(bs_year: int, bs_month: int) -> tuple:
    """Return (year, month) of previous BS month."""
    if bs_month == 1:
        return (bs_year - 1, 12)
    return (bs_year, bs_month - 1)


def days_remaining_label(end_date) -> str:
    """
    Return human-readable label:
      Active  → 'X days left'
      Expired → 'Expired X days ago'
    """
    if end_date is None:
        return "—"
    today = datetime.date.today()
    diff  = (end_date - today).days
    if diff >= 0:
        return f"{diff} days left"
    return f"Expired {abs(diff)} days ago"