# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Compose Regular Expressions from Patterns.

>>> version_info = PYCALVER_RE.match("v201712.0123-alpha").groupdict()
>>> assert version_info == {
...     "pycalver"    : "v201712.0123-alpha",
...     "vYYYYMM"     : "v201712",
...     "year"        : "2017",
...     "month"       : "12",
...     "build"       : ".0123",
...     "build_no"    : "0123",
...     "release"     : "-alpha",
...     "release_tag" : "alpha",
... }
>>>
>>> version_info = PYCALVER_RE.match("v201712.0033").groupdict()
>>> assert version_info == {
...     "pycalver"   : "v201712.0033",
...     "vYYYYMM"    : "v201712",
...     "year"       : "2017",
...     "month"      : "12",
...     "build"      : ".0033",
...     "build_no"   : "0033",
...     "release"    : None,
...     "release_tag": None,
... }
"""

import re
import typing as typ

# https://regex101.com/r/fnj60p/10
PYCALVER_PATTERN = r"""
\b
(?P<pycalver>
    (?P<vYYYYMM>
       v                        # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?P<build>
        \.                      # "." build nr prefix
        (?P<build_no>\d{4,})
    )
    (?P<release>
        \-                      # "-" release prefix
        (?P<release_tag>alpha|beta|dev|rc|post)
    )?
)(?:\s|$)
"""

PYCALVER_RE: typ.Pattern[str] = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)


PATTERN_ESCAPES = [
    ("\u005c", "\u005c\u005c"),
    ("-"     , "\u005c-"),
    ("."     , "\u005c."),
    ("+"     , "\u005c+"),
    ("*"     , "\u005c*"),
    ("?"     , "\u005c?"),
    ("{"     , "\u005c{"),
    ("}"     , "\u005c}"),
    ("["     , "\u005c["),
    ("]"     , "\u005c]"),
    ("("     , "\u005c("),
    (")"     , "\u005c)"),
]

COMPOSITE_PART_PATTERNS = {
    'pep440_pycalver': r"{year}{month}\.{BID}(?:{pep440_tag})?",
    'pycalver'       : r"v{year}{month}\.{bid}(?:-{tag})?",
    'calver'         : r"v{year}{month}",
    'semver'         : r"{MAJOR}\.{MINOR}\.{PATCH}",
    'release_tag'    : r"{tag}",
    'build'          : r"\.{bid}",
    'release'        : r"-{tag}",
    # depricated
    'pep440_version': r"{year}{month}\.{BID}(?:{pep440_tag})?",
}


PART_PATTERNS = {
    'year'      : r"\d{4}",
    'month'     : r"(?:0[0-9]|1[0-2])",
    'build_no'  : r"\d{4,}",
    'pep440_tag': r"(?:a|b|dev|rc|post)?\d*",
    'tag'       : r"(?:alpha|beta|dev|rc|post|final)",
    'yy'        : r"\d{2}",
    'yyyy'      : r"\d{4}",
    'quarter'   : r"[1-4]",
    'iso_week'  : r"(?:[0-4]\d|5[0-3])",
    'us_week'   : r"(?:[0-4]\d|5[0-3])",
    'dom'       : r"(0[1-9]|[1-2][0-9]|3[0-1])",
    'doy'       : r"(?:[0-2]\d\d|3[0-5][0-9]|36[0-6])",
    'MAJOR'     : r"\d+",
    'MINOR'     : r"\d+",
    'MM'        : r"\d{2,}",
    'MMM'       : r"\d{3,}",
    'MMMM'      : r"\d{4,}",
    'MMMMM'     : r"\d{5,}",
    'PATCH'     : r"\d+",
    'PP'        : r"\d{2,}",
    'PPP'       : r"\d{3,}",
    'PPPP'      : r"\d{4,}",
    'PPPPP'     : r"\d{5,}",
    'bid'       : r"\d{4,}",
    'BID'       : r"[1-9]\d*",
    'BB'        : r"[1-9]\d{1,}",
    'BBB'       : r"[1-9]\d{2,}",
    'BBBB'      : r"[1-9]\d{3,}",
    'BBBBB'     : r"[1-9]\d{4,}",
    'BBBBBB'    : r"[1-9]\d{5,}",
    'BBBBBBB'   : r"[1-9]\d{6,}",
}


FULL_PART_FORMATS = {
    'pep440_pycalver': "{year}{month:02}.{BID}{pep440_tag}",
    'pycalver'       : "v{year}{month:02}.{bid}{release}",
    'calver'         : "v{year}{month:02}",
    'semver'         : "{MAJOR}.{MINOR}.{PATCH}",
    'release_tag'    : "{tag}",
    'build'          : ".{bid}",
    # NOTE (mb 2019-01-04): since release is optional, it
    # is treates specially in version.format
    # 'release'       : "-{tag}",
    'month'   : "{month:02}",
    'build_no': "{bid}",
    'iso_week': "{iso_week:02}",
    'us_week' : "{us_week:02}",
    'dom'     : "{dom:02}",
    'doy'     : "{doy:03}",
    # depricated
    'pep440_version': "{year}{month:02}.{BID}{pep440_tag}",
    'version'       : "v{year}{month:02}.{bid}{release}",
}


PART_FORMATS = {
    'major'  : "[0-9]+",
    'minor'  : "[0-9]{3,}",
    'patch'  : "[0-9]{3,}",
    'bid'    : "[0-9]{4,}",
    'MAJOR'  : "[0-9]+",
    'MINOR'  : "[0-9]+",
    'MM'     : "[0-9]{2,}",
    'MMM'    : "[0-9]{3,}",
    'MMMM'   : "[0-9]{4,}",
    'MMMMM'  : "[0-9]{5,}",
    'MMMMMM' : "[0-9]{6,}",
    'MMMMMMM': "[0-9]{7,}",
    'PATCH'  : "[0-9]+",
    'PP'     : "[0-9]{2,}",
    'PPP'    : "[0-9]{3,}",
    'PPPP'   : "[0-9]{4,}",
    'PPPPP'  : "[0-9]{5,}",
    'PPPPPP' : "[0-9]{6,}",
    'PPPPPPP': "[0-9]{7,}",
    'BID'    : "[1-9][0-9]*",
    'BB'     : "[1-9][0-9]{1,}",
    'BBB'    : "[1-9][0-9]{2,}",
    'BBBB'   : "[1-9][0-9]{3,}",
    'BBBBB'  : "[1-9][0-9]{4,}",
    'BBBBBB' : "[1-9][0-9]{5,}",
    'BBBBBBB': "[1-9][0-9]{6,}",
}


def _replace_pattern_parts(pattern: str) -> str:
    for part_name, part_pattern in PART_PATTERNS.items():
        named_part_pattern = f"(?P<{part_name}>{part_pattern})"
        placeholder        = "\u005c{" + part_name + "\u005c}"
        pattern            = pattern.replace(placeholder, named_part_pattern)
    return pattern


def _compile_pattern(pattern: str) -> str:
    for char, escaped in PATTERN_ESCAPES:
        pattern = pattern.replace(char, escaped)

    return _replace_pattern_parts(pattern)


def compile_pattern(pattern: str) -> typ.Pattern[str]:
    pattern_str = _compile_pattern(pattern)
    return re.compile(pattern_str)


def _init_composite_patterns() -> None:
    for part_name, part_pattern in COMPOSITE_PART_PATTERNS.items():
        part_pattern = part_pattern.replace("{", "\u005c{").replace("}", "\u005c}")
        pattern_str  = _replace_pattern_parts(part_pattern)
        PART_PATTERNS[part_name] = pattern_str


_init_composite_patterns()
