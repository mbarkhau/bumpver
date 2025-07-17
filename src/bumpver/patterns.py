# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2025 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ


class Pattern(typ.NamedTuple):

    version_pattern: str  # "{pycalver}", "{year}.{month}", "vYYYY0M.BUILD"
    # This should be called 'norm_pattern' or similar:
    raw_pattern            : str  # '__version__ = "{version}"', "Copyright (c) YYYY"
    regexp                 : typ.Pattern[str]
    replacement_pattern    : str = None


RE_PATTERN_ESCAPES = [
    ("\u005c", "\u005c\u005c"),
    ("-"     , "\u005c-"),
    ("."     , "\u005c."),
    # ("+"     , "\u005c+"),
    # ("*"     , "\u005c*"),
    # ("?"     , "\u005c?"),
    ("{"     , "\u005c{"),
    ("}"     , "\u005c}"),
    ("["     , "\u005c["),
    ("]"     , "\u005c]"),
    ("("     , "\u005c("),
    (")"     , "\u005c)"),
]
