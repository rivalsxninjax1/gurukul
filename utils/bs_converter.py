"""
Bikram Sambat (BS) ↔ Gregorian (AD) converter.
Pure Python — no external dependencies.
Dates displayed in English numerals (2082-01-15 format).
"""

import datetime

# ── Lookup table: days per month per BS year ──────────────────────────────────
_BS_CALENDAR = {
    1970: [31,31,32,31,31,31,30,29,30,29,30,30],
    1971: [31,31,32,31,31,31,30,29,30,29,30,30],
    1972: [31,32,31,32,31,30,30,30,29,29,30,30],
    1973: [30,32,31,32,31,30,30,30,29,30,29,31],
    1974: [31,31,32,31,31,31,30,29,30,29,30,30],
    1975: [31,31,32,32,31,30,30,29,30,29,30,30],
    1976: [31,32,31,32,31,30,30,30,29,29,30,31],
    1977: [30,32,31,32,31,31,29,30,29,30,29,31],
    1978: [31,31,32,31,31,31,30,29,30,29,30,30],
    1979: [31,31,32,32,31,30,30,29,30,29,30,30],
    1980: [31,32,31,32,31,30,30,30,29,29,30,31],
    1981: [31,31,31,32,31,31,29,30,30,29,30,30],
    1982: [31,31,32,31,31,31,30,29,30,29,30,30],
    1983: [31,31,32,32,31,30,30,29,30,29,30,30],
    1984: [31,32,31,32,31,30,30,30,29,29,30,31],
    1985: [31,31,31,32,31,31,29,30,30,29,30,30],
    1986: [31,31,32,31,31,31,30,29,30,29,30,30],
    1987: [31,32,31,32,31,30,30,29,30,29,30,30],
    1988: [31,32,31,32,31,30,30,30,29,29,30,31],
    1989: [31,31,31,32,31,31,30,29,30,29,30,30],
    1990: [31,31,32,31,31,31,30,29,30,29,30,30],
    1991: [31,32,31,32,31,30,30,29,30,29,30,30],
    1992: [31,32,31,32,31,30,30,30,29,30,30,30],
    1993: [31,31,31,32,31,31,30,29,30,29,30,30],
    1994: [31,31,32,31,31,31,30,29,30,29,30,30],
    1995: [31,32,31,32,31,30,30,29,30,30,29,31],
    1996: [31,31,31,32,31,31,30,29,30,29,30,30],
    1997: [31,31,32,31,31,31,30,29,30,29,30,30],
    1998: [31,32,31,32,31,30,30,30,29,29,30,31],
    1999: [31,31,31,32,31,31,29,30,30,29,30,30],
    2000: [30,32,31,32,31,30,30,30,29,29,30,31],
    2001: [31,31,32,31,31,31,30,29,30,29,30,30],
    2002: [31,31,32,32,31,30,30,29,30,29,30,30],
    2003: [31,32,31,32,31,30,30,30,29,29,30,31],
    2004: [31,31,31,32,31,31,29,30,30,29,30,30],
    2005: [31,31,32,31,31,31,30,29,30,29,30,30],
    2006: [31,31,32,32,31,30,30,29,30,29,30,30],
    2007: [31,32,31,32,31,30,30,30,29,29,30,31],
    2008: [31,31,31,32,31,31,29,30,30,29,30,30],
    2009: [31,31,32,31,31,31,30,29,30,29,30,30],
    2010: [31,31,32,32,31,30,30,29,30,29,30,30],
    2011: [31,32,31,32,31,30,30,30,29,29,30,31],
    2012: [31,31,31,32,31,31,29,30,30,29,30,30],
    2013: [31,31,32,31,31,31,30,29,30,29,30,30],
    2014: [31,31,32,32,31,30,30,29,30,29,30,30],
    2015: [31,32,31,32,31,30,30,30,29,29,30,31],
    2016: [31,31,31,32,31,31,29,30,30,29,30,30],
    2017: [31,31,32,31,31,31,30,29,30,29,30,30],
    2018: [31,32,31,32,31,30,30,29,30,29,30,30],
    2019: [31,32,31,32,31,30,30,30,29,29,30,31],
    2020: [31,31,31,32,31,31,30,29,30,29,30,30],
    2021: [31,31,32,31,31,31,30,29,30,29,30,30],
    2022: [31,32,31,32,31,30,30,30,29,29,30,30],
    2023: [31,31,31,32,31,31,30,29,30,29,30,30],
    2024: [31,31,32,31,31,30,30,29,30,29,30,30],
    2025: [31,31,32,32,31,30,30,29,30,29,30,30],
    2026: [31,32,31,32,31,30,30,30,29,29,30,31],
    2027: [31,31,31,32,31,31,30,29,30,29,30,30],
    2028: [31,31,32,31,31,31,30,29,30,29,30,30],
    2029: [31,31,32,32,31,30,30,29,30,29,30,30],
    2030: [31,32,31,32,31,30,30,30,29,29,30,31],
    2031: [31,31,31,32,31,31,29,30,30,29,30,30],
    2032: [31,31,32,31,31,31,30,29,30,29,30,30],
    2033: [31,31,32,32,31,30,30,29,30,29,30,30],
    2034: [31,32,31,32,31,30,30,30,29,29,30,31],
    2035: [31,31,31,32,31,31,29,30,29,30,29,31],
    2036: [31,31,32,31,31,31,30,29,30,29,30,30],
    2037: [31,31,32,32,31,30,30,29,30,29,30,30],
    2038: [31,32,31,32,31,30,30,30,29,29,30,31],
    2039: [31,31,31,32,31,31,29,30,30,29,30,30],
    2040: [31,31,32,31,31,31,30,29,30,29,30,30],
    2041: [31,31,32,32,31,30,30,29,30,29,30,30],
    2042: [31,32,31,32,31,30,30,30,29,29,30,31],
    2043: [31,31,31,32,31,31,29,30,30,29,30,30],
    2044: [31,31,32,31,31,31,30,29,30,29,30,30],
    2045: [31,32,31,32,31,30,30,29,30,29,30,30],
    2046: [31,32,31,32,31,30,30,30,29,29,30,31],
    2047: [31,31,31,32,31,31,30,29,30,29,30,30],
    2048: [31,31,32,31,31,31,30,29,30,29,30,30],
    2049: [31,31,32,32,31,30,30,29,30,29,30,30],
    2050: [31,32,31,32,31,30,30,30,29,29,30,31],
    2051: [31,31,31,32,31,31,29,30,30,29,30,30],
    2052: [31,31,32,31,31,31,30,29,30,29,30,30],
    2053: [31,31,32,32,31,30,30,29,30,29,30,30],
    2054: [31,32,31,32,31,30,30,30,29,29,30,31],
    2055: [31,31,31,32,31,31,29,30,30,29,30,30],
    2056: [31,31,32,31,31,31,30,29,30,29,30,30],
    2057: [31,32,31,32,31,30,30,29,30,29,30,30],
    2058: [31,32,31,32,31,30,30,30,29,29,30,30],
    2059: [31,31,31,32,31,31,30,29,30,29,30,30],
    2060: [31,31,32,31,31,31,30,29,30,29,30,30],
    2061: [31,31,32,32,31,30,30,29,30,29,30,30],
    2062: [31,32,31,32,31,30,30,30,29,29,30,31],
    2063: [31,31,31,32,31,31,29,30,30,29,30,30],
    2064: [31,31,32,31,31,31,30,29,30,29,30,30],
    2065: [31,32,31,32,31,30,30,29,30,29,30,30],
    2066: [31,32,31,32,31,30,30,30,29,29,30,31],
    2067: [31,31,31,32,31,31,29,30,30,29,30,30],
    2068: [31,31,32,31,31,31,30,29,30,29,30,30],
    2069: [31,31,32,32,31,30,30,29,30,29,30,30],
    2070: [31,32,31,32,31,30,30,30,29,29,30,31],
    2071: [31,31,31,32,31,31,29,30,30,29,30,30],
    2072: [31,31,32,31,31,31,30,29,30,29,30,30],
    2073: [31,31,32,32,31,30,30,29,30,29,30,30],
    2074: [31,32,31,32,31,30,30,30,29,29,30,31],
    2075: [31,31,31,32,31,31,29,30,30,29,30,30],
    2076: [31,31,32,31,31,31,30,29,30,29,30,30],
    2077: [31,32,31,32,31,30,30,29,30,29,30,30],
    2078: [31,32,31,32,31,30,30,30,29,29,30,30],
    2079: [31,31,31,32,31,31,30,29,30,29,30,30],
    2080: [31,31,32,31,31,31,30,29,30,29,30,30],
    2081: [31,31,32,32,31,30,30,29,30,29,30,30],
    2082: [31,32,31,32,31,30,30,30,29,29,30,31],
    2083: [31,31,31,32,31,31,29,30,30,29,30,30],
    2084: [31,31,32,31,31,31,30,29,30,29,30,30],
    2085: [31,31,32,32,31,30,30,29,30,29,30,30],
    2086: [31,32,31,32,31,30,30,30,29,29,30,31],
    2087: [31,31,31,32,31,31,29,30,30,29,30,30],
    2088: [31,31,32,31,31,31,30,29,30,29,30,30],
    2089: [31,31,32,32,31,30,30,29,30,29,30,30],
    2090: [31,32,31,32,31,30,30,30,29,29,30,31],
}

# Epoch: BS 2000-09-17 = AD 1943-04-14
_BS_EPOCH = (2000, 9, 17)
_AD_EPOCH = datetime.date(1943, 4, 14)


# ── AD → BS ──────────────────────────────────────────────────────────────────

def ad_to_bs(ad_date) -> tuple:
    """
    Convert datetime.date (AD) → (bs_year, bs_month, bs_day).
    Returns (None, None, None) on failure.
    """
    if ad_date is None:
        return (None, None, None)
    try:
        days = (ad_date - _AD_EPOCH).days
    except Exception:
        return (None, None, None)

    if days < 0:
        return (None, None, None)

    bs_year, bs_month, bs_day = _BS_EPOCH

    while days > 0:
        if bs_year not in _BS_CALENDAR:
            return (None, None, None)
        days_in_month = _BS_CALENDAR[bs_year][bs_month - 1]
        remaining     = days_in_month - bs_day
        if days <= remaining:
            bs_day += days
            days = 0
        else:
            days     -= (remaining + 1)
            bs_day    = 1
            bs_month += 1
            if bs_month > 12:
                bs_month = 1
                bs_year += 1

    return (bs_year, bs_month, bs_day)


def bs_str(ad_date) -> str:
    """
    Return BS date string 'YYYY-MM-DD' from a datetime.date (AD).
    Falls back to str(ad_date) if conversion fails.
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
    """Convert an AD date string 'YYYY-MM-DD' → BS string."""
    if not date_str or date_str in ("—", ""):
        return date_str
    try:
        d = datetime.date.fromisoformat(date_str[:10])
        return bs_str(d)
    except Exception:
        return date_str


# ── BS → AD ──────────────────────────────────────────────────────────────────

def bs_to_ad(bs_year: int, bs_month: int, bs_day: int) -> datetime.date | None:
    """
    Convert BS date → datetime.date (AD).
    Returns None if invalid or out of range.
    """
    if bs_year not in _BS_CALENDAR:
        return None

    # Validate
    try:
        days_in_m = _BS_CALENDAR[bs_year][bs_month - 1]
    except (IndexError, KeyError):
        return None

    if bs_day < 1 or bs_day > days_in_m:
        return None

    # Count total days from BS epoch to target
    total_days = 0

    # Full years
    ey, em, ed = _BS_EPOCH
    cur_y, cur_m, cur_d = ey, em, ed

    # Days remaining in epoch month
    days_in_epoch_month = _BS_CALENDAR[ey][em - 1]
    remaining_in_first  = days_in_epoch_month - ed

    # Walk from epoch to target
    target_total = 0

    # Calculate days from BS epoch to start of target year
    tmp_y, tmp_m, tmp_d = _BS_EPOCH
    count = 0

    # Days left in starting month of epoch
    epoch_month_days = _BS_CALENDAR[tmp_y][tmp_m - 1]
    days_left_in_start = epoch_month_days - tmp_d  # days after epoch day

    if bs_year == tmp_y and bs_month == tmp_m:
        # Same month as epoch
        diff = bs_day - tmp_d
        if diff < 0:
            return None
        return _AD_EPOCH + datetime.timedelta(days=diff)

    # Move to end of epoch month
    count += days_left_in_start + 1  # +1 moves to first day of next month
    tmp_m += 1
    tmp_d  = 1
    if tmp_m > 12:
        tmp_m = 1
        tmp_y += 1

    # Walk month by month to target
    while not (tmp_y == bs_year and tmp_m == bs_month):
        if tmp_y not in _BS_CALENDAR:
            return None
        count   += _BS_CALENDAR[tmp_y][tmp_m - 1]
        tmp_m   += 1
        if tmp_m > 12:
            tmp_m = 1
            tmp_y += 1
        if tmp_y > bs_year + 1:
            return None

    # Add days within target month
    count += (bs_day - 1)

    try:
        return _AD_EPOCH + datetime.timedelta(days=count)
    except Exception:
        return None


def bs_to_ad_str(bs_str_val: str):
    """
    Parse 'YYYY-MM-DD' (BS) → datetime.date (AD).
    Returns None if invalid.
    """
    if not bs_str_val or bs_str_val == "—":
        return None
    try:
        parts = bs_str_val.strip().split("-")
        if len(parts) != 3:
            return None
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return bs_to_ad(y, m, d)
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def today_bs() -> str:
    """Return today's date in BS format 'YYYY-MM-DD'."""
    return bs_str(datetime.date.today())


def today_bs_tuple() -> tuple:
    """Return today's BS date as (year, month, day)."""
    return ad_to_bs(datetime.date.today())


def days_in_bs_month(bs_year: int, bs_month: int) -> int:
    """Return number of days in a given BS month."""
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
        max_day = _BS_CALENDAR[bs_year][bs_month - 1]
    except (IndexError, KeyError):
        return False
    return 1 <= bs_day <= max_day