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
from . import v1version
from .patterns import Pattern

logger = logging.getLogger("bumpver.v1rewrite")


def rewrite_lines(
    patterns : typ.List[Pattern],
    new_vinfo: version.V1VersionInfo,
    old_lines: typ.List[str],
) -> typ.List[str]:
    """Replace occurances of patterns in old_lines with new_vinfo."""
    found_patterns: typ.Set[Pattern] = set()

    new_lines = old_lines[:]
    for match in parse.iter_matches(old_lines, patterns):
        found_patterns.add(match.pattern)
        replacement = v1version.format_version(new_vinfo, match.pattern.raw_pattern)
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
    new_vinfo: version.V1VersionInfo,
    content  : str,
    path     : str = "<path>",
) -> rewrite.RewrittenFileData:
    r"""Rewrite pattern occurrences with version string.

    >>> version_pattern = "{pycalver}"
    >>> new_vinfo = v1version.parse_version_info("v201809.0123")

    >>> from .v1patterns import compile_pattern
    >>> patterns = [compile_pattern(version_pattern, '__version__ = "{pycalver}"')]

    >>> content = '__version__ = "v201809.0001-alpha"'
    >>> rfd = rfd_from_content(patterns, new_vinfo, content)
    >>> rfd.new_lines
    ['__version__ = "v201809.0123"']

    >>> patterns = [compile_pattern('{semver}', '__version__ = "v{semver}"')]
    >>> new_vinfo = v1version.parse_version_info("v1.2.3", "v{semver}")

    >>> content = '__version__ = "v1.2.2"'
    >>> rfd = rfd_from_content(patterns, new_vinfo, content)
    >>> rfd.new_lines
    ['__version__ = "v1.2.3"']
    """
    line_sep  = rewrite.detect_line_sep(content)
    old_lines = content.split(line_sep)
    new_lines = rewrite_lines(patterns, new_vinfo, old_lines)
    return rewrite.RewrittenFileData(path, line_sep, old_lines, new_lines)


def iter_rewritten(
    file_patterns: config.PatternsByFile,
    new_vinfo    : version.V1VersionInfo,
) -> typ.Iterable[rewrite.RewrittenFileData]:
    """Iterate over files with version string replaced."""

    fobj: typ.IO[str]

    for file_path, pattern_strs in rewrite.iter_path_patterns_items(file_patterns):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        rfd = rfd_from_content(pattern_strs, new_vinfo, content)
        yield rfd._replace(path=str(file_path))


def diff(
    old_vinfo    : version.V1VersionInfo,
    new_vinfo    : version.V1VersionInfo,
    file_patterns: config.PatternsByFile,
) -> str:
    """Generate diffs of rewritten files."""

    full_diff = ""
    fobj: typ.IO[str]

    for file_path, patterns in sorted(rewrite.iter_path_patterns_items(file_patterns)):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        has_updated_version = False
        for pattern in patterns:
            old_str = v1version.format_version(old_vinfo, pattern.raw_pattern)
            new_str = v1version.format_version(new_vinfo, pattern.raw_pattern)
            if old_str != new_str:
                has_updated_version = True

        try:
            rfd = rfd_from_content(patterns, new_vinfo, content)
        except rewrite.NoPatternMatch:
            # pylint:disable=raise-missing-from  ; we support py2, so not an option
            errmsg = f"No patterns matched for file '{file_path}'"
            raise rewrite.NoPatternMatch(errmsg)

        rfd   = rfd._replace(path=str(file_path))
        lines = rewrite.diff_lines(rfd)
        if len(lines) == 0 and has_updated_version:
            errmsg = f"No patterns matched for file '{file_path}'"
            raise rewrite.NoPatternMatch(errmsg)

        full_diff += "\n".join(lines) + "\n"

    full_diff = full_diff.rstrip("\n")
    return full_diff


def rewrite_files(
    file_patterns: config.PatternsByFile,
    new_vinfo    : version.V1VersionInfo,
) -> None:
    """Rewrite project files, updating each with the new version."""
    fobj: typ.IO[str]

    for file_data in iter_rewritten(file_patterns, new_vinfo):
        new_content = file_data.line_sep.join(file_data.new_lines)
        with io.open(file_data.path, mode="wt", encoding="utf-8") as fobj:
            fobj.write(new_content)
