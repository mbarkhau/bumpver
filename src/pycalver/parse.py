# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
"""Parse PyCalVer strings.

>>> version_info = PYCALVER_RE.match("v201712.0123-alpha").groupdict()
>>> assert version_info == {
...     "version" : "v201712.0123-alpha",
...     "calver"  : "v201712",
...     "year"    : "2017",
...     "month"   : "12",
...     "build"   : ".0123",
...     "release" : "-alpha",
... }
>>>
>>> version_info = PYCALVER_RE.match("v201712.0033").groupdict()
>>> assert version_info == {
...     "version" : "v201712.0033",
...     "calver"  : "v201712",
...     "year"    : "2017",
...     "month"   : "12",
...     "build"   : ".0033",
...     "release" : None,
... }
"""

import re
import logging
import typing as typ

from . import version

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


class VersionInfo(typ.NamedTuple):
    """Container for parsed version string."""

    version       : str
    pep440_version: str
    calver        : str
    year          : str
    month         : str
    build         : str
    release       : typ.Optional[str]


def parse_version_info(version_str: str) -> VersionInfo:
    """Parse a PyCalVer string.

    >>> vnfo = parse_version_info("v201712.0033-beta")
    >>> assert vnfo == VersionInfo(
    ...     version="v201712.0033-beta",
    ...     pep440_version="201712.33b0",
    ...     calver="v201712",
    ...     year="2017",
    ...     month="12",
    ...     build=".0033",
    ...     release="-beta",
    ... )
    """
    match = PYCALVER_RE.match(version_str)
    if match is None:
        raise ValueError(f"Invalid PyCalVer string: {version_str}")

    kwargs = match.groupdict()
    kwargs['pep440_version'] = version.pycalver_to_pep440(kwargs['version'])
    return VersionInfo(**kwargs)


class PatternMatch(typ.NamedTuple):
    """Container to mark a version string in a file."""

    lineno : int  # zero based
    line   : str
    pattern: str
    span   : typ.Tuple[int, int]
    match  : str


PatternMatches = typ.Iterable[PatternMatch]


def _iter_for_pattern(lines: typ.List[str], pattern: str) -> PatternMatches:
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
