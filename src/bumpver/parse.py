# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Parse PyCalVer strings from files."""

import typing as typ

from .patterns import Pattern

LineNo = int
Start  = int
End    = int


class LineSpan(typ.NamedTuple):
    lineno: LineNo
    start : Start
    end   : End


LineSpans = typ.List[LineSpan]


def _has_overlap(needle: LineSpan, haystack: LineSpans) -> bool:
    for span in haystack:
        # assume needle is in the center
        has_overlap = (
            span.lineno == needle.lineno
            # needle starts before (or at) span end
            and needle.start <= span.end
            # needle ends after (or at) span start
            and needle.end >= span.start
        )
        if has_overlap:
            return True

    return False


class PatternMatch(typ.NamedTuple):
    """Container to mark a version string in a file."""

    lineno : LineNo  # zero based
    line   : str
    pattern: Pattern
    span   : typ.Tuple[Start, End]
    match  : str


PatternMatches = typ.Iterable[PatternMatch]


def _iter_for_pattern(lines: typ.List[str], pattern: Pattern) -> PatternMatches:
    for lineno, line in enumerate(lines):
        match = pattern.regexp.search(line)
        if match and len(match.group(0)) > 0:
            yield PatternMatch(lineno, line, pattern, match.span(), match.group(0))


def iter_matches(lines: typ.List[str], patterns: typ.List[Pattern]) -> PatternMatches:
    """Iterate over all matches of any pattern on any line.

    >>> from . import v1patterns
    >>> lines = ["__version__ = 'v201712.0002-alpha'"]
    >>> version_pattern = "{pycalver}"
    >>> raw_patterns = ["{pycalver}", "{pep440_pycalver}"]
    >>> patterns = [v1patterns.compile_pattern(version_pattern, p) for p in raw_patterns]
    >>> matches = list(iter_matches(lines, patterns))
    >>> assert matches[0] == PatternMatch(
    ...     lineno = 0,
    ...     line   = "__version__ = 'v201712.0002-alpha'",
    ...     pattern= v1patterns.compile_pattern(version_pattern),
    ...     span   = (15, 33),
    ...     match  = "v201712.0002-alpha",
    ... )
    """
    matched_spans: LineSpans = []
    for pattern in patterns:
        for match in _iter_for_pattern(lines, pattern):
            needle_span = LineSpan(match.lineno, *match.span)
            if not _has_overlap(needle_span, matched_spans):
                yield match
            matched_spans.append(needle_span)
