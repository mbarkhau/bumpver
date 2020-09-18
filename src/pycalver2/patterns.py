# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Compose Regular Expressions from Patterns.

>>> pattern = compile_pattern("vYYYY0M.BUILD[-TAG]")
>>> version_info = pattern.regexp.match("v201712.0123-alpha")
>>> assert version_info.groupdict() == {
...     "version": "v201712.0123-alpha",
...     "year_y" : "2017",
...     "month"  : "12",
...     "bid"    : "0123",
...     "tag"    : "alpha",
... }
>>>
>>> version_info = pattern.regexp.match("201712.1234")
>>> assert version_info is None

>>> version_info = pattern.regexp.match("v201713.1234")
>>> assert version_info is None

>>> version_info = pattern.regexp.match("v201712.1234")
>>> assert version_info.groupdict() == {
...     "version": "v201712.1234",
...     "year_y" : "2017",
...     "month"  : "12",
...     "bid"    : "1234",
...     "tag"    : None,
... }
"""

import re
import typing as typ

import pycalver.patterns as v1patterns

PATTERN_ESCAPES = [
    ("\u005c", "\u005c\u005c"),
    ("-"     , "\u005c-"),
    ("."     , "\u005c."),
    ("+"     , "\u005c+"),
    ("*"     , "\u005c*"),
    ("?"     , "\u005c?"),
    ("{"     , "\u005c{"),
    ("}"     , "\u005c}"),
    # ("["     , "\u005c["),  # [braces] are used for optional parts
    # ("]"     , "\u005c]"),
    ("(", "\u005c("),
    (")", "\u005c)"),
]

# NOTE (mb 2020-09-17): For patterns with different options, the longer
#   patterns should be first/left (e.g. for 'MM', `1[0-2]` before `[1-9]`).
#   This ensures that the longest match is done rather than the shortest.
#   To have a consistent ordering, we always put the pattern that matches
#   the larger number first (even if the patterns would otherwise be the
#   same size).

PART_PATTERNS = {
    # Based on calver.org
    'YYYY': r"[1-9][0-9]{3}",
    'YY'  : r"[1-9][0-9]?",
    '0Y'  : r"[0-9]{2}",
    'GGGG': r"[1-9][0-9]{3}",
    'GG'  : r"[1-9][0-9]?",
    '0G'  : r"[0-9]{2}",
    'Q'   : r"[1-4]",
    'MM'  : r"(?:1[0-2]|[1-9])",
    '0M'  : r"(?:1[0-2]|0[1-9])",
    'DD'  : r"(?:3[0-1]|[1-2][0-9]|[1-9])",
    '0D'  : r"(?:3[0-1]|[1-2][0-9]|0[1-9])",
    'JJJ' : r"(?:36[0-6]|3[0-5][0-9]|[1-2][0-9][0-9]|[1-9][0-9]|[1-9])",
    '00J' : r"(?:36[0-6]|3[0-5][0-9]|[1-2][0-9][0-9]|0[1-9][0-9]|00[1-9])",
    # week numbering parts
    'WW': r"(?:5[0-2]|[1-4][0-9]|[0-9])",
    '0W': r"(?:5[0-2]|[0-4][0-9])",
    'UU': r"(?:5[0-2]|[1-4][0-9]|[0-9])",
    '0U': r"(?:5[0-2]|[0-4][0-9])",
    'VV': r"(?:5[0-3]|[1-4][0-9]|[1-9])",
    '0V': r"(?:5[0-3]|[1-4][0-9]|0[1-9])",
    # non calver parts
    'MAJOR': r"[0-9]+",
    'MINOR': r"[0-9]+",
    'PATCH': r"[0-9]+",
    'BUILD': r"[0-9]+",
    'BLD'  : r"[1-9][0-9]*",
    'TAG'  : r"(?:alpha|beta|dev|pre|rc|post|final)",
    'PYTAG': r"(?:a|b|dev|rc|post)",
    'NUM'  : r"[0-9]+",
}


PATTERN_PART_FIELDS = {
    'YYYY' : 'year_y',
    'YY'   : 'year_y',
    '0Y'   : 'year_y',
    'GGGG' : 'year_g',
    'GG'   : 'year_g',
    '0G'   : 'year_g',
    'Q'    : 'quarter',
    'MM'   : 'month',
    '0M'   : 'month',
    'DD'   : 'dom',
    '0D'   : 'dom',
    'JJJ'  : 'doy',
    '00J'  : 'doy',
    'MAJOR': 'major',
    'MINOR': 'minor',
    'PATCH': 'patch',
    'BUILD': 'bid',
    'BLD'  : 'bid',
    'TAG'  : 'tag',
    'PYTAG': 'pytag',
    'NUM'  : 'num',
    'WW'   : 'week_w',
    '0W'   : 'week_w',
    'UU'   : 'week_u',
    '0U'   : 'week_u',
    'VV'   : 'week_v',
    '0V'   : 'week_v',
}


FieldValue = typ.Union[str, int]


def _fmt_num(val: FieldValue) -> str:
    return str(val)


def _fmt_bld(val: FieldValue) -> str:
    return str(int(val))


def _fmt_yy(year_y: FieldValue) -> str:
    return str(int(str(year_y)[-2:]))


def _fmt_0y(year_y: FieldValue) -> str:
    return "{0:02}".format(int(str(year_y)[-2:]))


def _fmt_gg(year_g: FieldValue) -> str:
    return str(int(str(year_g)[-2:]))


def _fmt_0g(year_g: FieldValue) -> str:
    return "{0:02}".format(int(str(year_g)[-2:]))


def _fmt_0m(month: FieldValue) -> str:
    return "{0:02}".format(int(month))


def _fmt_0d(dom: FieldValue) -> str:
    return "{0:02}".format(int(dom))


def _fmt_00j(doy: FieldValue) -> str:
    return "{0:03}".format(int(doy))


def _fmt_0w(week_w: FieldValue) -> str:
    return "{0:02}".format(int(week_w))


def _fmt_0u(week_u: FieldValue) -> str:
    return "{0:02}".format(int(week_u))


def _fmt_0v(week_v: FieldValue) -> str:
    return "{0:02}".format(int(week_v))


PART_FORMATS: typ.Dict[str, typ.Callable[[FieldValue], str]] = {
    'YYYY' : _fmt_num,
    'YY'   : _fmt_yy,
    '0Y'   : _fmt_0y,
    'GGGG' : _fmt_num,
    'GG'   : _fmt_gg,
    '0G'   : _fmt_0g,
    'Q'    : _fmt_num,
    'MM'   : _fmt_num,
    '0M'   : _fmt_0m,
    'DD'   : _fmt_num,
    '0D'   : _fmt_0d,
    'JJJ'  : _fmt_num,
    '00J'  : _fmt_00j,
    'MAJOR': _fmt_num,
    'MINOR': _fmt_num,
    'PATCH': _fmt_num,
    'BUILD': _fmt_num,
    'BLD'  : _fmt_bld,
    'TAG'  : _fmt_num,
    'PYTAG': _fmt_num,
    'NUM'  : _fmt_num,
    'WW'   : _fmt_num,
    '0W'   : _fmt_0w,
    'UU'   : _fmt_num,
    '0U'   : _fmt_0u,
    'VV'   : _fmt_num,
    '0V'   : _fmt_0v,
}


def _replace_pattern_parts(pattern: str) -> str:
    # The pattern is escaped, so that everything besides the format
    # string variables is treated literally.
    if "[" in pattern and "]" in pattern:
        pattern = pattern.replace("[", "(?:")
        pattern = pattern.replace("]", ")?")

    part_patterns_by_index: typ.Dict[typ.Tuple[int, int], typ.Tuple[int, int, str]] = {}
    for part_name, part_pattern in PART_PATTERNS.items():
        start_idx = pattern.find(part_name)
        if start_idx < 0:
            continue

        field              = PATTERN_PART_FIELDS[part_name]
        named_part_pattern = f"(?P<{field}>{part_pattern})"
        end_idx            = start_idx + len(part_name)
        sort_key           = (-end_idx, -len(part_name))
        part_patterns_by_index[sort_key] = (start_idx, end_idx, named_part_pattern)

    # NOTE (mb 2020-09-17): The sorting is done so that we process items:
    #   - right before left
    #   - longer before shorter
    last_start_idx = len(pattern) + 1
    result_pattern = pattern
    for _, (start_idx, end_idx, named_part_pattern) in sorted(part_patterns_by_index.items()):
        if end_idx <= last_start_idx:
            result_pattern = (
                result_pattern[:start_idx] + named_part_pattern + result_pattern[end_idx:]
            )
            last_start_idx = start_idx

    return result_pattern


def compile_pattern_str(pattern: str) -> str:
    for char, escaped in PATTERN_ESCAPES:
        pattern = pattern.replace(char, escaped)

    return _replace_pattern_parts(pattern)


def compile_pattern(pattern: str) -> v1patterns.Pattern:
    pattern_str = compile_pattern_str(pattern)
    pattern_re  = re.compile(pattern_str)
    return v1patterns.Pattern(pattern, pattern_re)
