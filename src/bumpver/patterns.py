# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ


class Pattern(typ.NamedTuple):

    version_pattern: str  # "{pycalver}", "{year}.{month}", "vYYYY0M.BUILD"
    raw_pattern    : str  # '__version__ = "{version}"', "Copyright (c) YYYY"
    regexp         : typ.Pattern[str]


RE_PATTERN_ESCAPES = [
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
