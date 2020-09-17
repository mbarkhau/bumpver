# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Functions related to version string manipulation."""

import typing as typ
import logging
import datetime as dt

import lexid
import pkg_resources

import pycalver2.patterns as v2patterns

# import pycalver.version as v1version
# import pycalver.patterns as v1patterns

logger = logging.getLogger("pycalver.version")


# The test suite may replace this.
TODAY = dt.datetime.utcnow().date()


ID_FIELDS_BY_PART = {
    'MAJOR': 'major',
    'MINOR': 'minor',
    'PATCH': 'patch',
    'MICRO': 'patch',
}


ZERO_VALUES = {
    'major': "0",
    'minor': "0",
    'patch': "0",
    'tag'  : "final",
    'pytag': "",
    'num'  : "0",
}


TAG_BY_PEP440_TAG = {
    'a'   : 'alpha',
    'b'   : 'beta',
    ""    : 'final',
    'rc'  : 'rc',
    'dev' : 'dev',
    'post': 'post',
}


PEP440_TAG_BY_TAG = {
    'alpha': "a",
    'beta' : "b",
    'final': "",
    'pre'  : "rc",
    'rc'   : "rc",
    'dev'  : "dev",
    'post' : "post",
}

assert set(TAG_BY_PEP440_TAG.keys()) == set(PEP440_TAG_BY_TAG.values())
assert set(TAG_BY_PEP440_TAG.values()) < set(PEP440_TAG_BY_TAG.keys())

# PEP440_TAGS_REVERSE = {
#     "a"   : 'alpha',
#     "b"   : 'beta',
#     "rc"  : 'rc',
#     "dev" : 'dev',
#     "post": 'post',
# }


class CalendarInfo(typ.NamedTuple):
    """Container for calendar components of version strings."""

    year_y : int
    year_g : int
    quarter: int
    month  : int
    dom    : int
    doy    : int
    week_w : int
    week_u : int
    week_v : int


def _date_from_doy(year: int, doy: int) -> dt.date:
    """Parse date from year and day of year (1 indexed).

    >>> cases = [
    ...     (2016, 1), (2016, 31), (2016, 31 + 1), (2016, 31 + 29), (2016, 31 + 30),
    ...     (2017, 1), (2017, 31), (2017, 31 + 1), (2017, 31 + 28), (2017, 31 + 29),
    ... ]
    >>> dates = [_date_from_doy(year, month) for year, month in cases]
    >>> assert [(d.month, d.day) for d in dates] == [
    ...     (1, 1), (1, 31), (2, 1), (2, 29), (3, 1),
    ...     (1, 1), (1, 31), (2, 1), (2, 28), (3, 1),
    ... ]
    """
    return dt.date(year, 1, 1) + dt.timedelta(days=doy - 1)


def _quarter_from_month(month: int) -> int:
    """Calculate quarter (1 indexed) from month (1 indexed).

    >>> [_quarter_from_month(month) for month in range(1, 13)]
    [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
    """
    return ((month - 1) // 3) + 1


def cal_info(date: dt.date = None) -> CalendarInfo:
    """Generate calendar components for current date.

    >>> import datetime as dt

    >>> c = cal_info(dt.date(2019, 1, 5))
    >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.week_w, c.week_u, c.week_v)
    (2019, 1, 1, 5, 5, 0, 0, 1)

    >>> c = cal_info(dt.date(2019, 1, 6))
    >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.week_w, c.week_u, c.week_v)
    (2019, 1, 1, 6, 6, 0, 1, 1)

    >>> c = cal_info(dt.date(2019, 1, 7))
    >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.week_w, c.week_u, c.week_v)
    (2019, 1, 1, 7, 7, 1, 1, 2)

    >>> c = cal_info(dt.date(2019, 4, 7))
    >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.week_w, c.week_u, c.week_v)
    (2019, 2, 4, 7, 97, 13, 14, 14)
    """
    if date is None:
        date = TODAY

    kwargs = {
        'year_y' : date.year,
        'year_g' : int(date.strftime("%G"), base=10),
        'quarter': _quarter_from_month(date.month),
        'month'  : date.month,
        'dom'    : date.day,
        'doy'    : int(date.strftime("%j"), base=10),
        'week_w' : int(date.strftime("%W"), base=10),
        'week_u' : int(date.strftime("%U"), base=10),
        'week_v' : int(date.strftime("%V"), base=10),
    }

    return CalendarInfo(**kwargs)


MaybeInt = typ.Optional[int]


class VersionInfo(typ.NamedTuple):
    """Container for parsed version string."""

    year_y : MaybeInt
    year_g : MaybeInt
    quarter: MaybeInt
    month  : MaybeInt
    dom    : MaybeInt
    doy    : MaybeInt
    week_w : MaybeInt
    week_u : MaybeInt
    week_v : MaybeInt
    major  : int
    minor  : int
    patch  : int
    bid    : str
    tag    : str
    pytag  : str
    num    : MaybeInt


VALID_FIELD_KEYS = set(VersionInfo._fields) | {'version'}

FieldKey      = str
MatchGroupKey = str
MatchGroupStr = str

PatternGroups = typ.Dict[FieldKey, MatchGroupStr]
FieldValues   = typ.Dict[FieldKey, MatchGroupStr]


def _parse_version_info(field_values: FieldValues) -> VersionInfo:
    """Parse normalized VersionInfo from groups of a matched pattern.

    >>> vnfo = _parse_version_info({'year_y': "2018", 'month': "11", 'bid': "0099"})
    >>> (vnfo.year_y, vnfo.month, vnfo.quarter, vnfo.bid, vnfo.tag)
    (2018, 11, 4, '0099', 'final')

    >>> vnfo = _parse_version_info({'year_y': "2018", 'doy': "11", 'bid': "099", 'tag': "beta"})
    >>> (vnfo.year_y, vnfo.month, vnfo.dom, vnfo.doy, vnfo.bid, vnfo.tag)
    (2018, 1, 11, 11, '099', 'beta')

    >>> vnfo = _parse_version_info({'year_y': "2018", 'month': "6", 'dom': "15"})
    >>> (vnfo.year_y, vnfo.month, vnfo.dom, vnfo.doy)
    (2018, 6, 15, 166)

    >>> vnfo = _parse_version_info({'major': "1", 'minor': "23", 'patch': "45"})
    >>> (vnfo.major, vnfo.minor, vnfo.patch)
    (1, 23, 45)

    >>> vnfo = _parse_version_info({'major': "1", 'minor': "023", 'patch': "0045"})
    >>> (vnfo.major, vnfo.minor, vnfo.patch)
    (1, 23, 45)

    >>> vnfo = _parse_version_info({'year_y': "2021", 'week_w': "02"})
    >>> (vnfo.year_y, vnfo.week_w)
    (2021, 2)
    >>> vnfo = _parse_version_info({'year_y': "2021", 'week_u': "02"})
    >>> (vnfo.year_y, vnfo.week_u)
    (2021, 2)
    >>> vnfo = _parse_version_info({'year_g': "2021", 'week_v': "02"})
    >>> (vnfo.year_g, vnfo.week_v)
    (2021, 2)

    >>> vnfo = _parse_version_info({'year_y': "2021", 'month': "01", 'dom': "03"})
    >>> (vnfo.year_y, vnfo.month, vnfo.dom, vnfo.tag)
    (2021, 1, 3, 'final')
    >>> (vnfo.year_y, vnfo.week_w,vnfo.year_y, vnfo.week_u,vnfo.year_g, vnfo.week_v)
    (2021, 0, 2021, 1, 2020, 53)
    """
    for key in field_values:
        assert key in VALID_FIELD_KEYS, key

    fvals = field_values
    tag   = fvals.get('tag'  , "final")
    pytag = fvals.get('pytag', "")

    if tag and not pytag:
        pytag = PEP440_TAG_BY_TAG[tag]
    elif pytag and not tag:
        tag = TAG_BY_PEP440_TAG[pytag]

    num: MaybeInt = int(fvals['num']) if 'num' in fvals else None

    date: typ.Optional[dt.date] = None

    year_y: MaybeInt = int(fvals['year_y']) if 'year_y' in fvals else None
    year_g: MaybeInt = int(fvals['year_g']) if 'year_g' in fvals else None

    month: MaybeInt = int(fvals['month']) if 'month' in fvals else None
    doy  : MaybeInt = int(fvals['doy'  ]) if 'doy' in fvals else None
    dom  : MaybeInt = int(fvals['dom'  ]) if 'dom' in fvals else None

    week_w: MaybeInt = int(fvals['week_w']) if 'week_w' in fvals else None
    week_u: MaybeInt = int(fvals['week_u']) if 'week_u' in fvals else None
    week_v: MaybeInt = int(fvals['week_v']) if 'week_v' in fvals else None

    if year_y and doy:
        date  = _date_from_doy(year_y, doy)
        month = date.month
        dom   = date.day
    else:
        month = int(fvals['month']) if 'month' in fvals else None
        dom   = int(fvals['dom'  ]) if 'dom' in fvals else None

    if year_y and month and dom:
        date = dt.date(year_y, month, dom)

    if date:
        # derive all fields from other previous values
        year_y = int(date.strftime("%Y"), base=10)
        year_g = int(date.strftime("%G"), base=10)
        month  = int(date.strftime("%m"), base=10)
        dom    = int(date.strftime("%d"), base=10)
        doy    = int(date.strftime("%j"), base=10)
        week_w = int(date.strftime("%W"), base=10)
        week_u = int(date.strftime("%U"), base=10)
        week_v = int(date.strftime("%V"), base=10)

    quarter = int(fvals['quarter']) if 'quarter' in fvals else None
    if quarter is None and month:
        quarter = _quarter_from_month(month)

    major = int(fvals['major']) if 'major' in fvals else 0
    minor = int(fvals['minor']) if 'minor' in fvals else 0
    patch = int(fvals['patch']) if 'patch' in fvals else 0

    bid = fvals['bid'] if 'bid' in fvals else "1000"

    vnfo = VersionInfo(
        year_y=year_y,
        year_g=year_g,
        quarter=quarter,
        month=month,
        dom=dom,
        doy=doy,
        week_w=week_w,
        week_u=week_u,
        week_v=week_v,
        major=major,
        minor=minor,
        patch=patch,
        bid=bid,
        tag=tag,
        pytag=pytag,
        num=num,
    )
    return vnfo


VersionInfoKW = typ.Dict[str, typ.Union[str, int, None]]


class PatternError(Exception):
    pass


def parse_version_info(version_str: str, pattern: str = "vYYYY0M.BUILD[-TAG]") -> VersionInfo:
    """Parse normalized VersionInfo.

    >>> vnfo = parse_version_info("v201712.0033-beta", pattern="vYYYY0M.BUILD[-TAG]")
    >>> fvals = {'year_y': 2017, 'month': 12, 'bid': "0033", 'tag': "beta"}
    >>> assert vnfo == _parse_version_info(fvals)

    >>> vnfo = parse_version_info("1.23.456", pattern="MAJOR.MINOR.PATCH")
    >>> fvals = {'major': "1", 'minor': "23", 'patch': "456"}
    >>> assert vnfo == _parse_version_info(fvals)
    """
    pattern_tup = v2patterns.compile_pattern(pattern)
    match       = pattern_tup.regexp.match(version_str)
    if match is None:
        err_msg = (
            f"Invalid version string '{version_str}' "
            f"for pattern '{pattern}'/'{pattern_tup.regexp.pattern}'"
        )
        raise PatternError(err_msg)
    else:
        field_values = match.groupdict()
        return _parse_version_info(field_values)


def is_valid(version_str: str, pattern: str = "vYYYY0M.BUILD[-TAG]") -> bool:
    """Check if a version matches a pattern.

    >>> is_valid("v201712.0033-beta", pattern="vYYYY0M.BUILD[-TAG]")
    True
    >>> is_valid("v201712.0033-beta", pattern="MAJOR.MINOR.PATCH")
    False
    >>> is_valid("1.2.3", pattern="MAJOR.MINOR.PATCH")
    True
    >>> is_valid("v201712.0033-beta", pattern="MAJOR.MINOR.PATCH")
    False
    """
    try:
        parse_version_info(version_str, pattern)
        return True
    except PatternError:
        return False


TemplateKwargs = typ.Dict[str, typ.Union[str, int, None]]


def _format_part_values(vinfo: VersionInfo) -> typ.Dict[str, str]:
    """Generate kwargs for template from minimal VersionInfo.

    The VersionInfo Tuple only has the minimal representation
    of a parsed version, not the values suitable for formatting.
    It may for example have month=9, but not the formatted
    representation '09' for '0M'.

    >>> vinfo = parse_version_info("v200709.1033-beta", pattern="vYYYY0M.BUILD[-TAG]")
    >>> kwargs = _format_part_values(vinfo)
    >>> (kwargs['YYYY'], kwargs['0M'], kwargs['BUILD'], kwargs['TAG'])
    ('2007', '09', '1033', 'beta')
    >>> (kwargs['YY'], kwargs['0Y'], kwargs['MM'], kwargs['PYTAG'])
    ('7', '07', '9', 'b')
    """
    vnfo_kwargs: TemplateKwargs = vinfo._asdict()
    kwargs     : typ.Dict[str, str] = {}

    for part, field in v2patterns.PATTERN_PART_FIELDS.items():
        field_val = vnfo_kwargs[field]
        if field_val is None:
            continue

        format_fn = v2patterns.PART_FORMATS[part]
        kwargs[part] = format_fn(field_val)

    return kwargs


def format_version(vinfo: VersionInfo, pattern: str) -> str:
    """Generate version string.

    >>> import datetime as dt
    >>> vinfo = parse_version_info("v200712.0033-beta", pattern="vYYYY0M.BUILD[-TAG]")
    >>> vinfo_a = vinfo._replace(**cal_info(date=dt.date(2007, 1, 1))._asdict())
    >>> vinfo_b = vinfo._replace(**cal_info(date=dt.date(2007, 12, 31))._asdict())

    >>> format_version(vinfo_a, pattern="vYY.BUILD[-TAG]")
    'v7.33-beta'
    >>> format_version(vinfo_a, pattern="v0Y.BUILD[-TAG]")
    'v07.33-beta'
    >>> format_version(vinfo_a, pattern="YYYY0M.BUILD[PYTAG][NUM]")
    '201701.33b0'

    >>> format_version(vinfo_a, pattern="vYYYY0M.BUILD[-TAG]")
    'v201701.0033-beta'
    >>> format_version(vinfo_b, pattern="vYYYY0M.BUILD[-TAG]")
    'v201712.0033-beta'

    >>> format_version(vinfo_a, pattern="vYYYYwWW.BUILD[-TAG]")
    'v2017w00.33-beta'
    >>> format_version(vinfo_b, pattern="vYYYYwWW.BUILD[-TAG]")
    'v2017w52.33-beta'

    >>> format_version(vinfo_a, pattern="vYYYYdJJJ.BUILD[-TAG]")
    'v2017d001.0033-beta'
    >>> format_version(vinfo_b, pattern="vYYYYdJJJ.BUILD[-TAG]")
    'v2017d365.0033-beta'

    >>> format_version(vinfo_a, pattern="vGGGGwVV.BUILD[-TAG]")
    'v2016w52.0033-beta'

    >>> vinfo_c = vinfo_b._replace(major=1, minor=2, patch=34, tag='final')

    >>> format_version(vinfo_c, pattern="vYYYYwWW.BUILD-TAG")
    'v2017w52.33-final'
    >>> format_version(vinfo_c, pattern="vYYYYwWW.BUILD[-TAG]")
    'v2017w52.33'

    >>> format_version(vinfo_c, pattern="vMAJOR.MINOR.PATCH")
    'v1.2.34'

    >>> vinfo_d = vinfo_b._replace(major=1, minor=0, patch=0, tag='final')
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH-TAGNUM")
    'v1.0.0-final0'
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH-TAG[NUM]")
    'v1.0.0-final'
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH-TAG")
    'v1.0.0-final'
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH[-TAG]")
    'v1.0.0'
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR[.PATCH[-TAG]]")
    'v1.0'
    >>> format_version(vinfo_d, pattern="vMAJOR.MINOR[.MICRO[-TAG]]")
    'v1.0'
    >>> format_version(vinfo_d, pattern="vMAJOR[.MINOR[.PATCH[-TAG]]]")
    'v1'
    """
    kwargs      = _format_part_values(vinfo)
    part_values = sorted(kwargs.items(), key=lambda item: -len(item[0]))
    version     = pattern
    for part, value in part_values:
        version = version.replace(part, value)

    return version


def incr(
    old_version: str,
    pattern    : str = "vYYYY0M.BUILD[-TAG]",
    *,
    release: str  = None,
    major  : bool = False,
    minor  : bool = False,
    patch  : bool = False,
) -> typ.Optional[str]:
    """Increment version string.

    'old_version' is assumed to be a string that matches 'pattern'
    """
    try:
        old_vinfo = parse_version_info(old_version, pattern)
    except PatternError as ex:
        logger.error(str(ex))
        return None

    cur_vinfo = old_vinfo

    cur_cal_nfo = cal_info()

    old_date = (old_vinfo.year_y or 0, old_vinfo.month or 0, old_vinfo.dom or 0)
    cur_date = (cur_cal_nfo.year_y   , cur_cal_nfo.month   , cur_cal_nfo.dom)

    if old_date <= cur_date:
        cur_vinfo = cur_vinfo._replace(**cur_cal_nfo._asdict())
    else:
        logger.warning(f"Version appears to be from the future '{old_version}'")

    cur_vinfo = cur_vinfo._replace(bid=lexid.incr(cur_vinfo.bid))

    if major:
        cur_vinfo = cur_vinfo._replace(major=cur_vinfo.major + 1, minor=0, patch=0)
    if minor:
        cur_vinfo = cur_vinfo._replace(minor=cur_vinfo.minor + 1, patch=0)
    if patch:
        cur_vinfo = cur_vinfo._replace(patch=cur_vinfo.patch + 1)

    if release:
        cur_vinfo = cur_vinfo._replace(tag=release)

    new_version = format_version(cur_vinfo, pattern)
    if new_version == old_version:
        logger.error("Invalid arguments or pattern, version did not change.")
        return None
    else:
        return new_version


def to_pep440(version: str) -> str:
    """Derive pep440 compliant version string from PyCalVer version string.

    >>> to_pep440("v201811.0007-beta")
    '201811.7b0'
    """
    return str(pkg_resources.parse_version(version))
