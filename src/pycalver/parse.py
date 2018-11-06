# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT

import re
import logging
import typing as typ
import pkg_resources


log = logging.getLogger("pycalver.parse")


VALID_RELESE_VALUES = ("alpha", "beta", "dev", "rc", "post")


# https://regex101.com/r/fnj60p/10
PYCALVER_PATTERN = r"""
\b
(?P<version>
    (?P<calver>
       v                        # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?P<build>
        \.                      # "." build nr prefix
        \d{4,}
    )
    (?P<release>
        \-                      # "-" release prefix
        (?:alpha|beta|dev|rc|post)
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
    ("["     , "\u005c["),
    ("("     , "\u005c("),
]

# NOTE (mb 2018-09-03): These are matchers for parts, which are
#   used in the patterns, they're not for validation. This means
#   that they may find strings, which are not valid pycalver
#   strings, when parsed in their full context. For such cases,
#   the patterns should be expanded.


RE_PATTERN_PARTS = {
    'pep440_version': r"\d{6}\.[1-9]\d*(a|b|dev|rc|post)?\d*",
    'version'       : r"v\d{6}\.\d{4,}(\-(alpha|beta|dev|rc|post))?",
    'calver'        : r"v\d{6}",
    'build'         : r"\.\d{4,}",
    'release'       : r"(\-(alpha|beta|dev|rc|post))?",
}


class PatternMatch(typ.NamedTuple):

    lineno : int  # zero based
    line   : str
    pattern: str
    span   : typ.Tuple[int, int]
    match  : str


class VersionInfo(typ.NamedTuple):

    pep440_version: str
    version       : str
    calver        : str
    year          : str
    month         : str
    build         : str
    release       : typ.Optional[str]


def parse_version_info(version: str) -> VersionInfo:
    match = PYCALVER_RE.match(version)
    if match is None:
        raise ValueError(f"Invalid pycalver: {version}")
    pep440_version = str(pkg_resources.parse_version(version))
    return VersionInfo(pep440_version=pep440_version, **match.groupdict())


def _iter_pattern_matches(lines: typ.List[str], pattern: str) -> typ.Iterable[PatternMatch]:
    # The pattern is escaped, so that everything besides the format
    # string variables is treated literally.

    pattern_tmpl = pattern

    for char, escaped in PATTERN_ESCAPES:
        pattern_tmpl = pattern_tmpl.replace(char, escaped)

    pattern_str = pattern_tmpl.format(**RE_PATTERN_PARTS)
    pattern_re  = re.compile(pattern_str)
    for lineno, line in enumerate(lines):
        match = pattern_re.search(line)
        if match:
            yield PatternMatch(lineno, line, pattern, match.span(), match.group(0))


def parse_patterns(lines: typ.List[str], patterns: typ.List[str]) -> typ.List[PatternMatch]:
    all_matches: typ.List[PatternMatch] = []
    for pattern in patterns:
        all_matches.extend(_iter_pattern_matches(lines, pattern))
    return all_matches
