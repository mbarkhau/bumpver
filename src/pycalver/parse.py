# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Parse PyCalVer strings from files."""

import typing as typ

import pycalver.patterns as v1patterns


class PatternMatch(typ.NamedTuple):
    """Container to mark a version string in a file."""

    lineno : int  # zero based
    line   : str
    pattern: v1patterns.Pattern
    span   : typ.Tuple[int, int]
    match  : str


PatternMatches = typ.Iterable[PatternMatch]


def _iter_for_pattern(lines: typ.List[str], pattern: v1patterns.Pattern) -> PatternMatches:
    for lineno, line in enumerate(lines):
        match = pattern.regexp.search(line)
        if match:
            yield PatternMatch(lineno, line, pattern, match.span(), match.group(0))


def iter_matches(lines: typ.List[str], patterns: typ.List[v1patterns.Pattern]) -> PatternMatches:
    """Iterate over all matches of any pattern on any line.

    >>> import pycalver.patterns as v1patterns
    >>> lines = ["__version__ = 'v201712.0002-alpha'"]
    >>> patterns = ["{pycalver}", "{pep440_pycalver}"]
    >>> patterns = [v1patterns.compile_pattern(p) for p in patterns]
    >>> matches = list(iter_matches(lines, patterns))
    >>> assert matches[0] == PatternMatch(
    ...     lineno = 0,
    ...     line   = "__version__ = 'v201712.0002-alpha'",
    ...     pattern= v1patterns.compile_pattern("{pycalver}"),
    ...     span   = (15, 33),
    ...     match  = "v201712.0002-alpha",
    ... )
    """
    for pattern in patterns:
        for match in _iter_for_pattern(lines, pattern):
            yield match
