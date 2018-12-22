# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
"""Parse PyCalVer strings from files."""

import re
import logging
import typing as typ

log = logging.getLogger("pycalver.parse")


VALID_RELEASE_VALUES = ("alpha", "beta", "dev", "rc", "post", "final")


PATTERN_ESCAPES = [
    ("\u005c", "\u005c\u005c"),
    ("-"     , "\u005c-"),
    ("."     , "\u005c."),
    ("+"     , "\u005c+"),
    ("*"     , "\u005c*"),
    ("{"     , "\u005c{{"),
    ("}"     , "\u005c}}"),
    ("["     , "\u005c["),
    ("]"     , "\u005c]"),
    ("("     , "\u005c("),
    (")"     , "\u005c)"),
]

# NOTE (mb 2018-09-03): These are matchers for parts, which are
#   used in the patterns, they're not for validation. This means
#   that they may find strings, which are not valid pycalver
#   strings, when parsed in their full context. For such cases,
#   the patterns should be expanded.


RE_PATTERN_PARTS = {
    'pep440_version': r"\d{6}\.[1-9]\d*(a|b|dev|rc|post)?\d*",
    'version'       : r"v\d{6}\.\d{4,}(\-(alpha|beta|dev|rc|post|final))?",
    'calver'        : r"v\d{6}",
    'year'          : r"\d{4}",
    'month'         : r"\d{2}",
    'build'         : r"\.\d{4,}",
    'build_no'      : r"\d{4,}",
    'release'       : r"(\-(alpha|beta|dev|rc|post|final))?",
    'release_tag'   : r"(alpha|beta|dev|rc|post|final)?",
}


class PatternMatch(typ.NamedTuple):
    """Container to mark a version string in a file."""

    lineno : int  # zero based
    line   : str
    pattern: str
    span   : typ.Tuple[int, int]
    match  : str


PatternMatches = typ.Iterable[PatternMatch]


def compile_pattern(pattern: str) -> typ.Pattern[str]:
    pattern_tmpl = pattern

    for char, escaped in PATTERN_ESCAPES:
        pattern_tmpl = pattern_tmpl.replace(char, escaped)

    # undo escaping only for valid part names
    for part_name in RE_PATTERN_PARTS.keys():
        pattern_tmpl = pattern_tmpl.replace(
            "\u005c{{" + part_name + "\u005c}}", "{" + part_name + "}"
        )

    pattern_str = pattern_tmpl.format(**RE_PATTERN_PARTS)
    return re.compile(pattern_str)


def _iter_for_pattern(lines: typ.List[str], pattern: str) -> PatternMatches:
    # The pattern is escaped, so that everything besides the format
    # string variables is treated literally.
    pattern_re = compile_pattern(pattern)

    for lineno, line in enumerate(lines):
        match = pattern_re.search(line)
        if match:
            yield PatternMatch(lineno, line, pattern, match.span(), match.group(0))


def iter_matches(lines: typ.List[str], patterns: typ.List[str]) -> PatternMatches:
    """Iterate over all matches of any pattern on any line.

    >>> lines = ["__version__ = 'v201712.0002-alpha'"]
    >>> patterns = ["{version}", "{pep440_version}"]
    >>> matches = list(iter_matches(lines, patterns))
    >>> assert matches[0] == PatternMatch(
    ...     lineno = 0,
    ...     line   = "__version__ = 'v201712.0002-alpha'",
    ...     pattern= "{version}",
    ...     span   = (15, 33),
    ...     match  = "v201712.0002-alpha",
    ... )
    """
    for pattern in patterns:
        for match in _iter_for_pattern(lines, pattern):
            yield match
