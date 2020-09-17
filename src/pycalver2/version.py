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

# import pycalver.patterns as v1patterns
import pycalver2.patterns as v2patterns

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
    'TAG'  : "final",
    'PYTAG': "",
}


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
    # TODO reenable doctest
    # """Generate calendar components for current date.

    # >>> from datetime import date

    # >>> c = cal_info(date(2019, 1, 5))
    # >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    # (2019, 1, 1, 5, 5, 0, 0)

    # >>> c = cal_info(date(2019, 1, 6))
    # >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    # (2019, 1, 1, 6, 6, 0, 1)

    # >>> c = cal_info(date(2019, 1, 7))
    # >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    # (2019, 1, 1, 7, 7, 1, 1)

    # >>> c = cal_info(date(2019, 4, 7))
    # >>> (c.year_y, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    # (2019, 2, 4, 7, 97, 13, 14)
    # """
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


class VersionInfo(typ.NamedTuple):
    """Container for parsed version string."""

    year_y : typ.Optional[int]
    year_g : typ.Optional[int]
    quarter: typ.Optional[int]
    month  : typ.Optional[int]
    dom    : typ.Optional[int]
    doy    : typ.Optional[int]
    week_w : typ.Optional[int]
    week_u : typ.Optional[int]
    week_v : typ.Optional[int]
    major  : int
    minor  : int
    patch  : int
    bid    : str
    tag    : str
    pytag  : str


FieldKey      = str
MatchGroupKey = str
MatchGroupStr = str

PatternGroups = typ.Dict[MatchGroupKey, MatchGroupStr]
FieldValues   = typ.Dict[FieldKey     , MatchGroupStr]


def _parse_field_values(field_values: FieldValues) -> VersionInfo:
    fvals = field_values
    tag   = fvals.get('tag')
    if tag is None:
        tag = "final"

    tag = TAG_ALIASES.get(tag, tag)
    assert tag is not None
    # TODO (mb 2020-09-06): parts of course
    pytag = "TODO"

    bid = fvals['bid'] if 'bid' in fvals else "1001"

    year_y = int(fvals['year_y']) if 'year_y' in fvals else None
    year_g = int(fvals['year_g']) if 'year_g' in fvals else None
    doy    = int(fvals['doy'   ]) if 'doy' in fvals else None

    date: typ.Optional[dt.date] = None

    month: typ.Optional[int] = None
    dom  : typ.Optional[int] = None

    week_w: typ.Optional[int] = None
    week_u: typ.Optional[int] = None
    week_v: typ.Optional[int] = None

    if year_y and doy:
        date  = _date_from_doy(year_y, doy)
        month = date.month
        dom   = date.day
    else:
        month = int(fvals['month']) if 'month' in fvals else None
        dom   = int(fvals['dom'  ]) if 'dom' in fvals else None

    quarter = int(fvals['quarter']) if 'quarter' in fvals else None
    if quarter is None and month:
        quarter = _quarter_from_month(month)

    if year_y and month and dom:
        date = dt.date(year_y, month, dom)

    if date:
        # derive all fields from other previous values
        doy    = int(date.strftime("%j"), base=10)
        week_w = int(date.strftime("%W"), base=10)
        week_u = int(date.strftime("%U"), base=10)
        week_v = int(date.strftime("%V"), base=10)
        year_g = int(date.strftime("%G"), base=10)

    major = int(fvals['major']) if 'major' in fvals else 0
    minor = int(fvals['minor']) if 'minor' in fvals else 0
    patch = int(fvals['patch']) if 'patch' in fvals else 0

    return VersionInfo(
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
    )


def _is_calver(nfo: typ.Union[CalendarInfo, VersionInfo]) -> bool:
    # TODO reenable doctest
    # """Check pattern for any calendar based parts.

    # >>> _is_calver(cal_info())
    # True

    # >>> vnfo = _parse_version_info({'year': "2018", 'month': "11", 'bid': "0018"})
    # >>> _is_calver(vnfo)
    # True

    # >>> vnfo = _parse_version_info({'MAJOR': "1", 'MINOR': "023", 'PATCH': "45"})
    # >>> _is_calver(vnfo)
    # False
    # """
    for field in CalendarInfo._fields:
        maybe_val: typ.Any = getattr(nfo, field, None)
        if isinstance(maybe_val, int):
            return True

    return False


TAG_ALIASES: typ.Dict[str, str] = {
    'a'  : "alpha",
    'b'  : "beta",
    'pre': "rc",
}


PEP440_TAGS: typ.Dict[str, str] = {
    'alpha': "a",
    'beta' : "b",
    'final': "",
    'rc'   : "rc",
    'dev'  : "dev",
    'post' : "post",
}


VersionInfoKW = typ.Dict[str, typ.Union[str, int, None]]


class PatternError(Exception):
    pass


def _parse_pattern_groups(pattern_groups: PatternGroups) -> FieldValues:
    for part_name in pattern_groups.keys():
        is_valid_part_name = (
            part_name in v2patterns.COMPOSITE_PART_PATTERNS or part_name in PATTERN_PART_FIELDS
        )
        if not is_valid_part_name:
            err_msg = f"Invalid part '{part_name}'"
            raise PatternError(err_msg)

    field_value_items = [
        (field_name, pattern_groups[part_name])
        for part_name, field_name in PATTERN_PART_FIELDS.items()
        if part_name in pattern_groups.keys()
    ]

    all_fields       = [field_name for field_name, _ in field_value_items]
    unique_fields    = set(all_fields)
    duplicate_fields = [f for f in unique_fields if all_fields.count(f) > 1]

    if any(duplicate_fields):
        err_msg = f"Multiple parts for same field {duplicate_fields}."
        raise PatternError(err_msg)

    return dict(field_value_items)


def _parse_version_info(pattern_groups: PatternGroups) -> VersionInfo:
    # TODO reenable doctest
    # """Parse normalized VersionInfo from groups of a matched pattern.

    # >>> vnfo = _parse_version_info({'year': "2018", 'month': "11", 'bid': "0099"})
    # >>> (vnfo.year_y, vnfo.month, vnfo.quarter, vnfo.bid, vnfo.tag)
    # (2018, 11, 4, '0099', 'final')

    # >>> vnfo = _parse_version_info({'year': "2018", 'doy': "11", 'bid': "099", 'tag': "b"})
    # >>> (vnfo.year_y, vnfo.month, vnfo.dom, vnfo.bid, vnfo.tag)
    # (2018, 1, 11, '099', 'beta')

    # >>> vnfo = _parse_version_info({'MAJOR': "1", 'MINOR': "23", 'PATCH': "45"})
    # >>> (vnfo.major, vnfo.minor, vnfo.patch)
    # (1, 23, 45)

    # >>> vnfo = _parse_version_info({'MAJOR': "1", 'MMM': "023", 'PPPP': "0045"})
    # >>> (vnfo.major, vnfo.minor, vnfo.patch)
    # (1, 23, 45)
    # """
    field_values = _parse_pattern_groups(pattern_groups)
    return _parse_field_values(field_values)


def parse_version_info(version_str: str, pattern: str = "vYYYY0M.BUILD[-TAG]") -> VersionInfo:
    # """Parse normalized VersionInfo.

    # >>> vnfo = parse_version_info("v201712.0033-beta", pattern="vYYYY0M.BUILD[-TAG]")
    # >>> assert vnfo == _parse_version_info({'year': 2017, 'month': 12, 'bid': "0033", 'tag': "beta"})

    # >>> vnfo = parse_version_info("1.23.456", pattern="MAJOR.MINOR.PATCH")
    # >>> assert vnfo == _parse_version_info({'MAJOR': "1", 'MINOR': "23", 'PATCH': "456"})
    # """
    pattern_tup = v2patterns.compile_pattern(pattern)
    match       = pattern_tup.regexp.match(version_str)
    if match is None:
        err_msg = (
            f"Invalid version string '{version_str}' "
            f"for pattern '{pattern}'/'{pattern_tup.regexp.pattern}'"
        )
        raise PatternError(err_msg)

    return _parse_version_info(match.groupdict())


def is_valid(version_str: str, pattern: str = "{pycalver}") -> bool:
    # TODO reenable doctest
    # """Check if a version matches a pattern.

    # >>> is_valid("v201712.0033-beta", pattern="{pycalver}")
    # True
    # >>> is_valid("v201712.0033-beta", pattern="{semver}")
    # False
    # >>> is_valid("1.2.3", pattern="{semver}")
    # True
    # >>> is_valid("v201712.0033-beta", pattern="{semver}")
    # False
    # """
    try:
        parse_version_info(version_str, pattern)
        return True
    except PatternError:
        return False


TemplateKwargs = typ.Dict[str, typ.Union[str, int, None]]


def _derive_template_kwargs(vinfo: VersionInfo) -> TemplateKwargs:
    """Generate kwargs for template from minimal VersionInfo.

    The VersionInfo Tuple only has the minimal representation
    of a parsed version, not the values suitable for formatting.
    It may for example have month=9, but not the formatted
    representation '09' for '0M'.
    """
    kwargs: TemplateKwargs = vinfo._asdict()

    tag = vinfo.tag
    kwargs['TAG'] = tag
    if tag == 'final':
        kwargs['PYTAG'] = ""
    else:
        kwargs['PYTAG'] = PEP440_TAGS[tag] + "0"

    year_y = vinfo.year_y
    if year_y:
        kwargs['0Y'  ] = str(year_y)[-2:]
        kwargs['YY'  ] = int(str(year_y)[-2:])
        kwargs['YYYY'] = year_y

    year_g = vinfo.year_g
    if year_g:
        kwargs['0G'  ] = str(year_g)[-2:]
        kwargs['GG'  ] = int(str(year_g)[-2:])
        kwargs['GGGG'] = year_g

    kwargs['BUILD'] = int(vinfo.bid, 10)

    for part_name, field in ID_FIELDS_BY_PART.items():
        val = kwargs[field]
        if part_name.lower() == field.lower():
            if isinstance(val, str):
                kwargs[part_name] = int(val, base=10)
            else:
                kwargs[part_name] = val
        else:
            assert len(set(part_name)) == 1
            padded_len = len(part_name)
            kwargs[part_name] = str(val).zfill(padded_len)

    return kwargs


def _compile_format_template(pattern: str, kwargs: TemplateKwargs) -> str:
    # NOTE (mb 2020-09-04): Some parts are optional, we need the kwargs to
    #   determine if part is set to its zero value
    format_tmpl = pattern
    for part_name, full_part_format in v2patterns.FULL_PART_FORMATS.items():
        format_tmpl = format_tmpl.replace("{" + part_name + "}", full_part_format)
    return format_tmpl


def format_version(vinfo: VersionInfo, pattern: str) -> str:
    # TODO reenable doctest
    # """Generate version string.

    # >>> import datetime as dt
    # >>> vinfo = parse_version_info("v201712.0033-beta", pattern="{pycalver}")
    # >>> vinfo_a = vinfo._replace(**cal_info(date=dt.date(2017, 1, 1))._asdict())
    # >>> vinfo_b = vinfo._replace(**cal_info(date=dt.date(2017, 12, 31))._asdict())

    # >>> format_version(vinfo_a, pattern="v{yy}.{BID}{release}")
    # 'v17.33-beta'
    # >>> format_version(vinfo_a, pattern="vYY.BUILD[-TAG]")
    # 'v17.33-beta'
    # >>> format_version(vinfo_a, pattern="YYYY0M.BUILD[PYTAG]")
    # '201701.33b0'

    # >>> format_version(vinfo_a, pattern="{pycalver}")
    # 'v201701.0033-beta'
    # >>> format_version(vinfo_b, pattern="{pycalver}")
    # 'v201712.0033-beta'

    # >>> format_version(vinfo_a, pattern="v{year}w{iso_week}.{BID}{release}")
    # 'v2017w00.33-beta'
    # >>> format_version(vinfo_a, pattern="vYYYYwWW.BUILD[-TAG]")
    # 'v2017w00.33-beta'
    # >>> format_version(vinfo_b, pattern="v{year}w{iso_week}.{BID}{release}")
    # 'v2017w52.33-beta'
    # >>> format_version(vinfo_b, pattern="vYYYYwWW.BUILD[-TAG]")
    # 'v2017w52.33-beta'

    # >>> format_version(vinfo_a, pattern="v{year}d{doy}.{bid}{release}")
    # 'v2017d001.0033-beta'
    # >>> format_version(vinfo_b, pattern="v{year}d{doy}.{bid}{release}")
    # 'v2017d365.0033-beta'
    # >>> format_version(vinfo_a, pattern="vYYYYdJJJ.BUILD[-TAG]")
    # 'v2017d001.0033-beta'
    # >>> format_version(vinfo_b, pattern="vYYYYdJJJ.BUILD[-TAG]")
    # 'v2017d365.0033-beta'

    # >>> format_version(vinfo_a, pattern="vGGGGwVV.BUILD[-TAG]")
    # 'v2016w52.0033-beta'

    # >>> vinfo_c = vinfo_b._replace(major=1, minor=2, patch=34, tag='final')

    # >>> format_version(vinfo_c, pattern="v{year}w{iso_week}.{BID}-{tag}")
    # 'v2017w52.33-final'
    # >>> format_version(vinfo_c, pattern="v{year}w{iso_week}.{BID}{release}")
    # 'v2017w52.33'
    # >>> format_version(vinfo_c, pattern="vYYYYwWW.BUILD-TAG")
    # 'v2017w52.33-final'
    # >>> format_version(vinfo_c, pattern="vYYYYwWW.BUILD[-TAG]")
    # 'v2017w52.33'

    # >>> format_version(vinfo_c, pattern="v{MAJOR}.{MINOR}.{PATCH}")
    # 'v1.2.34'
    # >>> format_version(vinfo_c, pattern="vMAJOR.MINOR.PATCH")
    # 'v1.2.34'

    # >>> vinfo_d = vinfo_b._replace(major=1, minor=0, patch=0, tag='final')
    # >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH-TAG")
    # 'v1.0.0-final'
    # >>> format_version(vinfo_d, pattern="vMAJOR.MINOR.PATCH[-TAG]")
    # 'v1.0.0'
    # >>> format_version(vinfo_d, pattern="vMAJOR.MINOR[.PATCH[-TAG]]")
    # 'v1.0'
    # >>> format_version(vinfo_d, pattern="vMAJOR.MINOR[.MICRO[-TAG]]")
    # 'v1.0'
    # >>> format_version(vinfo_d, pattern="vMAJOR[.MINOR[.PATCH[-TAG]]]")
    # 'v1'
    # """
    kwargs      = _derive_template_kwargs(vinfo)
    format_tmpl = _compile_format_template(pattern, kwargs)

    return format_tmpl.format(**kwargs)


def incr(
    old_version: str,
    pattern    : str = "{pycalver}",
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
