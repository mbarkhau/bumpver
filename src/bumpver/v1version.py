# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Functions related to version string manipulation."""

import typing as typ
import logging
import datetime as dt

import lexid

from . import version
from . import v1patterns

logger = logging.getLogger("bumpver.v1version")


CalInfo = typ.Union[version.V1CalendarInfo, version.V1VersionInfo]


def _is_cal_gt(left: CalInfo, right: CalInfo) -> bool:
    """Is left > right for non-None fields."""

    lvals = []
    rvals = []
    for field in version.V1CalendarInfo._fields:
        lval = getattr(left , field)
        rval = getattr(right, field)
        if not (lval is None or rval is None):
            lvals.append(lval)
            rvals.append(rval)

    return lvals > rvals


def _ver_to_cal_info(vnfo: version.V1VersionInfo) -> version.V1CalendarInfo:
    return version.V1CalendarInfo(
        vnfo.year,
        vnfo.quarter,
        vnfo.month,
        vnfo.dom,
        vnfo.doy,
        vnfo.iso_week,
        vnfo.us_week,
    )


def cal_info(date: dt.date = None) -> version.V1CalendarInfo:
    """Generate calendar components for current date.

    >>> from datetime import date

    >>> c = cal_info(date(2019, 1, 5))
    >>> (c.year, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    (2019, 1, 1, 5, 5, 0, 0)

    >>> c = cal_info(date(2019, 1, 6))
    >>> (c.year, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    (2019, 1, 1, 6, 6, 0, 1)

    >>> c = cal_info(date(2019, 1, 7))
    >>> (c.year, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    (2019, 1, 1, 7, 7, 1, 1)

    >>> c = cal_info(date(2019, 4, 7))
    >>> (c.year, c.quarter, c.month, c.dom, c.doy, c.iso_week, c.us_week)
    (2019, 2, 4, 7, 97, 13, 14)
    """
    if date is None:
        date = version.TODAY

    kwargs = {
        'year'    : date.year,
        'quarter' : version.quarter_from_month(date.month),
        'month'   : date.month,
        'dom'     : date.day,
        'doy'     : int(date.strftime("%j"), base=10),
        'iso_week': int(date.strftime("%W"), base=10),
        'us_week' : int(date.strftime("%U"), base=10),
    }

    return version.V1CalendarInfo(**kwargs)


FieldKey      = str
MatchGroupKey = str
MatchGroupStr = str

PatternGroups = typ.Dict[MatchGroupKey, MatchGroupStr]
FieldValues   = typ.Dict[FieldKey     , MatchGroupStr]


def _parse_field_values(field_values: FieldValues) -> version.V1VersionInfo:
    fvals = field_values
    tag   = fvals.get('tag')
    if tag is None:
        tag = "final"
    tag = version.TAG_BY_PEP440_TAG.get(tag, tag)
    assert tag is not None

    bid = fvals['bid'] if 'bid' in fvals else "0001"

    year = int(fvals['year']) if 'year' in fvals else None
    if year is not None and year < 100:
        year += 2000

    doy = int(fvals['doy']) if 'doy' in fvals else None

    month: typ.Optional[int]
    dom  : typ.Optional[int]

    if year and doy:
        date  = version.date_from_doy(year, doy)
        month = date.month
        dom   = date.day
    else:
        month = int(fvals['month']) if 'month' in fvals else None
        dom   = int(fvals['dom'  ]) if 'dom' in fvals else None

    iso_week: typ.Optional[int]
    us_week : typ.Optional[int]

    if year and month and dom:
        date     = dt.date(year, month, dom)
        doy      = int(date.strftime("%j"), base=10)
        iso_week = int(date.strftime("%W"), base=10)
        us_week  = int(date.strftime("%U"), base=10)
    else:
        iso_week = None
        us_week  = None

    quarter = int(fvals['quarter']) if 'quarter' in fvals else None
    if quarter is None and month:
        quarter = version.quarter_from_month(month)

    major = int(fvals['major']) if 'major' in fvals else 0
    minor = int(fvals['minor']) if 'minor' in fvals else 0
    patch = int(fvals['patch']) if 'patch' in fvals else 0

    return version.V1VersionInfo(
        year=year,
        quarter=quarter,
        month=month,
        dom=dom,
        doy=doy,
        iso_week=iso_week,
        us_week=us_week,
        major=major,
        minor=minor,
        patch=patch,
        bid=bid,
        tag=tag,
    )


def _is_calver(cinfo: CalInfo) -> bool:
    """Check pattern for any calendar based parts.

    >>> _is_calver(cal_info())
    True

    >>> vnfo = _parse_version_info({'year': "2018", 'month': "11", 'bid': "0018"})
    >>> _is_calver(vnfo)
    True

    >>> vnfo = _parse_version_info({'MAJOR': "1", 'MINOR': "023", 'PATCH': "45"})
    >>> _is_calver(vnfo)
    False
    """
    for field in version.V1CalendarInfo._fields:
        maybe_val: typ.Any = getattr(cinfo, field, None)
        if isinstance(maybe_val, int):
            return True

    return False


VersionInfoKW = typ.Dict[str, typ.Union[str, int, None]]


def _parse_pattern_groups(pattern_groups: PatternGroups) -> FieldValues:
    for part_name in pattern_groups.keys():
        is_valid_part_name = (
            part_name    in v1patterns.COMPOSITE_PART_PATTERNS
            or part_name in v1patterns.PATTERN_PART_FIELDS
        )
        if not is_valid_part_name:
            err_msg = f"Invalid part '{part_name}'"
            raise version.PatternError(err_msg)

    field_value_items = [
        (field_name, pattern_groups[part_name])
        for part_name, field_name in v1patterns.PATTERN_PART_FIELDS.items()
        if part_name in pattern_groups.keys()
    ]

    all_fields       = [field_name for field_name, _ in field_value_items]
    unique_fields    = set(all_fields)
    duplicate_fields = [f for f in unique_fields if all_fields.count(f) > 1]

    if any(duplicate_fields):
        err_msg = f"Multiple parts for same field {duplicate_fields}."
        raise version.PatternError(err_msg)
    else:
        return dict(field_value_items)


def _parse_version_info(pattern_groups: PatternGroups) -> version.V1VersionInfo:
    """Parse normalized V1VersionInfo from groups of a matched pattern.

    >>> vnfo = _parse_version_info({'year': "2018", 'month': "11", 'bid': "0099"})
    >>> (vnfo.year, vnfo.month, vnfo.quarter, vnfo.bid, vnfo.tag)
    (2018, 11, 4, '0099', 'final')

    >>> vnfo = _parse_version_info({'year': "18", 'month': "11"})
    >>> (vnfo.year, vnfo.month, vnfo.quarter)
    (2018, 11, 4)

    >>> vnfo = _parse_version_info({'year': "2018", 'doy': "11", 'bid': "099", 'tag': "b"})
    >>> (vnfo.year, vnfo.month, vnfo.dom, vnfo.bid, vnfo.tag)
    (2018, 1, 11, '099', 'beta')

    >>> vnfo = _parse_version_info({'MAJOR': "1", 'MINOR': "23", 'PATCH': "45"})
    >>> (vnfo.major, vnfo.minor, vnfo.patch)
    (1, 23, 45)

    >>> vnfo = _parse_version_info({'MAJOR': "1", 'MMM': "023", 'PPPP': "0045"})
    >>> (vnfo.major, vnfo.minor, vnfo.patch)
    (1, 23, 45)
    """
    field_values = _parse_pattern_groups(pattern_groups)
    return _parse_field_values(field_values)


def parse_version_info(version_str: str, raw_pattern: str = "{pycalver}") -> version.V1VersionInfo:
    """Parse normalized V1VersionInfo.

    >>> vnfo = parse_version_info("v201712.0033-beta", raw_pattern="{pycalver}")
    >>> assert vnfo == _parse_version_info({'year': 2017, 'month': 12, 'bid': "0033", 'tag': "beta"})

    >>> vnfo = parse_version_info("1.23.456", raw_pattern="{semver}")
    >>> assert vnfo == _parse_version_info({'MAJOR': "1", 'MINOR': "23", 'PATCH': "456"})
    """
    pattern = v1patterns.compile_pattern(raw_pattern)
    match   = pattern.regexp.match(version_str)
    if match is None:
        err_msg = (
            f"Invalid version string '{version_str}' "
            f"for pattern '{raw_pattern}'/'{pattern.regexp.pattern}'"
        )
        raise version.PatternError(err_msg)
    else:
        return _parse_version_info(match.groupdict())


def is_valid(version_str: str, raw_pattern: str = "{pycalver}") -> bool:
    """Check if a version matches a pattern.

    >>> is_valid("v201712.0033-beta", raw_pattern="{pycalver}")
    True
    >>> is_valid("v201712.0033-beta", raw_pattern="{semver}")
    False
    >>> is_valid("1.2.3", raw_pattern="{semver}")
    True
    >>> is_valid("v201712.0033-beta", raw_pattern="{semver}")
    False
    """
    try:
        parse_version_info(version_str, raw_pattern)
        return True
    except version.PatternError:
        return False


ID_FIELDS_BY_PART = {
    'MAJOR'  : 'major',
    'MINOR'  : 'minor',
    'MM'     : 'minor',
    'MMM'    : 'minor',
    'MMMM'   : 'minor',
    'MMMMM'  : 'minor',
    'MMMMMM' : 'minor',
    'MMMMMMM': 'minor',
    'PATCH'  : 'patch',
    'PP'     : 'patch',
    'PPP'    : 'patch',
    'PPPP'   : 'patch',
    'PPPPP'  : 'patch',
    'PPPPPP' : 'patch',
    'PPPPPPP': 'patch',
    'BID'    : 'bid',
    'BB'     : 'bid',
    'BBB'    : 'bid',
    'BBBB'   : 'bid',
    'BBBBB'  : 'bid',
    'BBBBBB' : 'bid',
    'BBBBBBB': 'bid',
}


def format_version(vinfo: version.V1VersionInfo, raw_pattern: str) -> str:
    """Generate version string.

    >>> import datetime as dt
    >>> vinfo = parse_version_info("v201712.0033-beta", raw_pattern="{pycalver}")
    >>> vinfo_a = vinfo._replace(**cal_info(date=dt.date(2017, 1, 1))._asdict())
    >>> vinfo_b = vinfo._replace(**cal_info(date=dt.date(2017, 12, 31))._asdict())
    >>> vinfo_c = vinfo_b._replace(major=1, minor=2, patch=34, tag='final')

    >>> format_version(vinfo_a, raw_pattern="v{yy}.{BID}{release}")
    'v17.33-beta'
    >>> format_version(vinfo_a, raw_pattern="{pep440_version}")
    '201701.33b0'

    >>> format_version(vinfo_a, raw_pattern="{pycalver}")
    'v201701.0033-beta'
    >>> format_version(vinfo_b, raw_pattern="{pycalver}")
    'v201712.0033-beta'

    >>> format_version(vinfo_a, raw_pattern="v{year}w{iso_week}.{BID}{release}")
    'v2017w00.33-beta'
    >>> format_version(vinfo_b, raw_pattern="v{year}w{iso_week}.{BID}{release}")
    'v2017w52.33-beta'

    >>> format_version(vinfo_a, raw_pattern="v{year}d{doy}.{bid}{release}")
    'v2017d001.0033-beta'
    >>> format_version(vinfo_b, raw_pattern="v{year}d{doy}.{bid}{release}")
    'v2017d365.0033-beta'

    >>> format_version(vinfo_c, raw_pattern="v{year}w{iso_week}.{BID}-{tag}")
    'v2017w52.33-final'
    >>> format_version(vinfo_c, raw_pattern="v{year}w{iso_week}.{BID}{release}")
    'v2017w52.33'

    >>> format_version(vinfo_c, raw_pattern="v{MAJOR}.{MINOR}.{PATCH}")
    'v1.2.34'
    >>> format_version(vinfo_c, raw_pattern="v{MAJOR}.{MM}.{PPP}")
    'v1.02.034'
    """
    full_pattern = raw_pattern
    for part_name, full_part_format in v1patterns.FULL_PART_FORMATS.items():
        full_pattern = full_pattern.replace("{" + part_name + "}", full_part_format)

    kwargs: typ.Dict[str, typ.Union[str, int, None]] = vinfo._asdict()

    release_tag = vinfo.tag
    if release_tag == 'final':
        kwargs['release'   ] = ""
        kwargs['pep440_tag'] = ""
    else:
        kwargs['release'   ] = "-" + release_tag
        kwargs['pep440_tag'] = version.PEP440_TAG_BY_TAG[release_tag] + "0"

    kwargs['release_tag'] = release_tag

    year = vinfo.year
    if year:
        kwargs['yy'  ] = str(year)[-2:]
        kwargs['yyyy'] = year

    kwargs['BID'] = int(vinfo.bid, 10)

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

    return full_pattern.format(**kwargs)


def incr(
    old_version: str,
    raw_pattern: str = "{pycalver}",
    *,
    major   : bool = False,
    minor   : bool = False,
    patch   : bool = False,
    tag     : typ.Optional[str] = None,
    tag_num : bool = False,
    pin_date: bool = False,
    date    : typ.Optional[dt.date] = None,
) -> typ.Optional[str]:
    """Increment version string.

    'old_version' is assumed to be a string that matches 'pattern'
    """
    try:
        old_vinfo = parse_version_info(old_version, raw_pattern)
    except version.PatternError as ex:
        logger.error(str(ex))
        return None

    cur_cinfo = _ver_to_cal_info(old_vinfo) if pin_date else cal_info(date)

    if _is_cal_gt(old_vinfo, cur_cinfo):
        logger.warning(f"Old version appears to be from the future '{old_version}'")
        cur_vinfo = old_vinfo
    else:
        cur_vinfo = old_vinfo._replace(**cur_cinfo._asdict())

    cur_vinfo = cur_vinfo._replace(bid=lexid.next_id(cur_vinfo.bid))

    if major:
        cur_vinfo = cur_vinfo._replace(major=cur_vinfo.major + 1, minor=0, patch=0)
    if minor:
        cur_vinfo = cur_vinfo._replace(minor=cur_vinfo.minor + 1, patch=0)
    if patch:
        cur_vinfo = cur_vinfo._replace(patch=cur_vinfo.patch + 1)
    if tag_num:
        raise NotImplementedError("--tag-num not supported for old style patterns")
    if tag:
        cur_vinfo = cur_vinfo._replace(tag=tag)

    new_version = format_version(cur_vinfo, raw_pattern)
    if new_version == old_version:
        logger.error("Invalid arguments or pattern, version did not change.")
        return None
    else:
        return new_version
