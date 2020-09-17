# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
# """Compose Regular Expressions from Patterns.

# >>> pattern = compile_pattern("vYYYY0M.BUILD[-TAG]")
# >>> version_info = pattern.regexp.match("v201712.0123-alpha")
# >>> assert version_info == {
# ...     "version": "v201712.0123-alpha",
# ...     "YYYY"   : "2017",
# ...     "0M"     : "12",
# ...     "BUILD"  : "0123",
# ...     "TAG"    : "alpha",
# ... }
# >>>
# >>> version_info = pattern.regexp.match("201712.1234")
# >>> assert version_info is None

# >>> version_info = pattern.regexp.match("v201712.1234")
# >>> assert version_info == {
# ...     "version": "v201712.0123-alpha",
# ...     "YYYY"   : "2017",
# ...     "0M"     : "12",
# ...     "BUILD"  : "0123",
# ...     "TAG"    : None,
# ... }
# """

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
    ("["     , "\u005c["),
    ("]"     , "\u005c]"),
    ("("     , "\u005c("),
    (")"     , "\u005c)"),
]


PART_PATTERNS = {
    # Based on calver.org
    'YYYY': r"[1-9][0-9]{3}",
    'YY'  : r"[1-9][0-9]?",
    '0Y'  : r"[0-9]{2}",
    'Q'   : r"[1-4]",
    'MM'  : r"(?:[1-9]|1[0-2])",
    '0M'  : r"(?:0[1-9]|1[0-2])",
    'DD'  : r"(?:[1-9]|[1-2][0-9]|3[0-1])",
    '0D'  : r"(?:0[1-9]|[1-2][0-9]|3[0-1])",
    'JJJ' : r"(?:[1-9]|[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6])",
    '00J' : r"(?:00[1-9]|0[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6])",
    # week numbering parts
    'WW'  : r"(?:[0-9]|[1-4][0-9]|5[0-2])",
    '0W'  : r"(?:[0-4][0-9]|5[0-2])",
    'UU'  : r"(?:[0-9]|[1-4][0-9]|5[0-2])",
    '0U'  : r"(?:[0-4][0-9]|5[0-2])",
    'VV'  : r"(?:[1-9]|[1-4][0-9]|5[0-3])",
    '0V'  : r"(?:0[1-9]|[1-4][0-9]|5[0-3])",
    'GGGG': r"[1-9][0-9]{3}",
    'GG'  : r"[1-9][0-9]?",
    '0G'  : r"[0-9]{2}",
    # non calver parts
    'MAJOR': r"[0-9]+",
    'MINOR': r"[0-9]+",
    'PATCH': r"[0-9]+",
    'MICRO': r"[0-9]+",
    'BUILD': r"[0-9]+",
    'TAG'  : r"(?:alpha|beta|dev|rc|post|final)",
    'PYTAG': r"(?:a|b|dev|rc|post)?[0-9]*",
}


def _replace_pattern_parts(pattern: str) -> str:
    # The pattern is escaped, so that everything besides the format
    # string variables is treated literally.
    for part_name, part_pattern in PART_PATTERNS.items():
        named_part_pattern = f"(?P<{part_name}>{part_pattern})"
        placeholder        = "\u005c{" + part_name + "\u005c}"
        pattern            = pattern.replace(placeholder, named_part_pattern)
    return pattern


def compile_pattern_str(pattern: str) -> str:
    for char, escaped in PATTERN_ESCAPES:
        pattern = pattern.replace(char, escaped)

    return _replace_pattern_parts(pattern)


def compile_pattern(pattern: str) -> v1patterns.Pattern:
    pattern_str = compile_pattern_str(pattern)
    pattern_re  = re.compile(pattern_str)
    return v1patterns.Pattern(pattern, pattern_re)
