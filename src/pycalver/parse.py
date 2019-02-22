# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Parse PyCalVer strings from files."""

import logging
import typing as typ

from . import patterns

log = logging.getLogger("pycalver.parse")


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
    pattern_re = patterns.compile_pattern(pattern)

    for lineno, line in enumerate(lines):
        match = pattern_re.search(line)
        if match:
            yield PatternMatch(lineno, line, pattern, match.span(), match.group(0))


def iter_matches(lines: typ.List[str], patterns: typ.List[str]) -> PatternMatches:
    """Iterate over all matches of any pattern on any line.

    >>> lines = ["__version__ = 'v201712.0002-alpha'"]
    >>> patterns = ["{pycalver}", "{pep440_pycalver}"]
    >>> matches = list(iter_matches(lines, patterns))
    >>> assert matches[0] == PatternMatch(
    ...     lineno = 0,
    ...     line   = "__version__ = 'v201712.0002-alpha'",
    ...     pattern= "{pycalver}",
    ...     span   = (15, 33),
    ...     match  = "v201712.0002-alpha",
    ... )
    """
    for pattern in patterns:
        for match in _iter_for_pattern(lines, pattern):
            yield match
