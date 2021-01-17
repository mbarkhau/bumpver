# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Rewrite files, updating occurences of version strings."""

import io
import typing as typ
import logging

from . import parse
from . import config
from . import rewrite
from . import version
from . import regexfmt
from . import v2version
from . import v2patterns
from .patterns import Pattern

logger = logging.getLogger("bumpver.v2rewrite")


def rewrite_lines(
    patterns : typ.List[Pattern],
    new_vinfo: version.V2VersionInfo,
    old_lines: typ.List[str],
) -> typ.List[str]:
    """Replace occurances of patterns in old_lines with new_vinfo."""
    found_patterns: typ.Set[Pattern] = set()

    new_lines = old_lines[:]
    for match in parse.iter_matches(old_lines, patterns):
        found_patterns.add(match.pattern)
        normalized_pattern = v2patterns.normalize_pattern(
            match.pattern.version_pattern, match.pattern.raw_pattern
        )
        replacement = v2version.format_version(new_vinfo, normalized_pattern)
        span_l, span_r = match.span
        new_line = match.line[:span_l] + replacement + match.line[span_r:]
        new_lines[match.lineno] = new_line

    non_matched_patterns = set(patterns) - found_patterns
    if non_matched_patterns:
        for nmp in non_matched_patterns:
            logger.error(f"No match for pattern '{nmp.raw_pattern}'")
            msg = (
                "\n# "
                + regexfmt.regex101_url(nmp.regexp.pattern)
                + "\nregex = "
                + regexfmt.pyexpr_regex(nmp.regexp.pattern)
            )
            logger.error(msg)
        raise rewrite.NoPatternMatch("Invalid pattern(s)")
    else:
        return new_lines


def rfd_from_content(
    patterns : typ.List[Pattern],
    new_vinfo: version.V2VersionInfo,
    content  : str,
    path     : str = "<path>",
) -> rewrite.RewrittenFileData:
    r"""Rewrite pattern occurrences with version string.

    >>> from .v2patterns import compile_pattern
    >>> version_pattern = "vYYYY0M.BUILD[-TAG]"
    >>> new_vinfo = v2version.parse_version_info("v201809.0123", version_pattern)
    >>> patterns = [compile_pattern(version_pattern, '__version__ = "vYYYY0M.BUILD[-TAG]"')]
    >>> content = '__version__ = "v201809.0001-alpha"'
    >>> rfd = rfd_from_content(patterns, new_vinfo, content)
    >>> rfd.new_lines
    ['__version__ = "v201809.0123"']

    >>> version_pattern = "vMAJOR.MINOR.PATCH"
    >>> new_vinfo = v2version.parse_version_info("v1.2.3", version_pattern)
    >>> patterns = [compile_pattern(version_pattern, '__version__ = "vMAJOR.MINOR.PATCH"')]
    >>> content = '__version__ = "v1.2.2"'
    >>> rfd = rfd_from_content(patterns, new_vinfo, content)
    >>> rfd.new_lines
    ['__version__ = "v1.2.3"']
    """
    line_sep  = rewrite.detect_line_sep(content)
    old_lines = content.split(line_sep)
    new_lines = rewrite_lines(patterns, new_vinfo, old_lines)
    return rewrite.RewrittenFileData(path, line_sep, old_lines, new_lines)


def _patterns_with_change(
    old_vinfo: version.V2VersionInfo, new_vinfo: version.V2VersionInfo, patterns: typ.List[Pattern]
) -> int:
    patterns_with_change = 0
    for pattern in patterns:
        old_str = v2version.format_version(old_vinfo, pattern.raw_pattern)
        new_str = v2version.format_version(new_vinfo, pattern.raw_pattern)
        if old_str != new_str:
            patterns_with_change += 1
    return patterns_with_change


def iter_rewritten(
    file_patterns: config.PatternsByFile,
    new_vinfo    : version.V2VersionInfo,
) -> typ.Iterable[rewrite.RewrittenFileData]:
    """Iterate over files with version string replaced."""

    fobj: typ.IO[str]

    for file_path, patterns in rewrite.iter_path_patterns_items(file_patterns):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        rfd = rfd_from_content(patterns, new_vinfo, content)
        yield rfd._replace(path=str(file_path))


def diff(
    old_vinfo    : version.V2VersionInfo,
    new_vinfo    : version.V2VersionInfo,
    file_patterns: config.PatternsByFile,
) -> str:
    r"""Generate diffs of rewritten files."""

    full_diff = ""
    fobj: typ.IO[str]

    for file_path, patterns in sorted(rewrite.iter_path_patterns_items(file_patterns)):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        try:
            rfd = rfd_from_content(patterns, new_vinfo, content)
        except rewrite.NoPatternMatch:
            # pylint:disable=raise-missing-from  ; we support py2, so not an option
            errmsg = f"No patterns matched for file '{file_path}'"
            raise rewrite.NoPatternMatch(errmsg)

        rfd   = rfd._replace(path=str(file_path))
        lines = rewrite.diff_lines(rfd)

        patterns_with_change = _patterns_with_change(old_vinfo, new_vinfo, patterns)
        if len(lines) == 0 and patterns_with_change > 0:
            errmsg = f"No patterns matched for file '{file_path}'"
            raise rewrite.NoPatternMatch(errmsg)

        full_diff += "\n".join(lines) + "\n"

    full_diff = full_diff.rstrip("\n")
    return full_diff


def rewrite_files(
    file_patterns: config.PatternsByFile,
    new_vinfo    : version.V2VersionInfo,
) -> None:
    """Rewrite project files, updating each with the new version."""
    fobj: typ.IO[str]

    for file_data in iter_rewritten(file_patterns, new_vinfo):
        new_content = file_data.line_sep.join(file_data.new_lines)
        with io.open(file_data.path, mode="wt", encoding="utf-8") as fobj:
            fobj.write(new_content)
