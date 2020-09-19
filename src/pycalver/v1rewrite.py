# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Rewrite files, updating occurences of version strings."""

import io
import typing as typ
import logging

from . import parse
from . import config
from . import rewrite
from . import version
from . import v1version
from .patterns import Pattern

logger = logging.getLogger("pycalver.v1rewrite")


def rewrite_lines(
    patterns : typ.List[Pattern],
    new_vinfo: version.V1VersionInfo,
    old_lines: typ.List[str],
) -> typ.List[str]:
    """Replace occurances of patterns in old_lines with new_vinfo.

    >>> from .v1patterns import compile_pattern
    >>> version_pattern = "{pycalver}"
    >>> new_vinfo = v1version.parse_version_info("v201811.0123-beta", version_pattern)
    >>> patterns = [compile_pattern(version_pattern, '__version__ = "{pycalver}"')]
    >>> rewrite_lines(patterns, new_vinfo, ['__version__ = "v201809.0002-beta"'])
    ['__version__ = "v201811.0123-beta"']

    >>> patterns = [compile_pattern(version_pattern, '__version__ = "{pep440_version}"')]
    >>> rewrite_lines(patterns, new_vinfo, ['__version__ = "201809.2b0"'])
    ['__version__ = "201811.123b0"']
    """
    new_lines      = old_lines[:]
    found_patterns = set()

    for match in parse.iter_matches(old_lines, patterns):
        found_patterns.add(match.pattern.raw_pattern)
        replacement = v1version.format_version(new_vinfo, match.pattern.raw_pattern)
        span_l, span_r = match.span
        new_line = match.line[:span_l] + replacement + match.line[span_r:]
        new_lines[match.lineno] = new_line

    non_matched_patterns = set(patterns) - found_patterns
    if non_matched_patterns:
        for nmp in non_matched_patterns:
            logger.error(f"No match for pattern '{nmp.raw_pattern}'")
            logger.error(f"Pattern compiles to regex '{nmp.regexp.pattern}'")
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

    >>> from .v1patterns import compile_pattern
    >>> patterns = [compile_pattern("{pycalver}", '__version__ = "{pycalver}"']
    >>> new_vinfo = v1version.parse_version_info("v201809.0123")

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
    r'''Iterate over files with version string replaced.

    >>> version_pattern = "{pycalver}"
    >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    >>> new_vinfo = v1version.parse_version_info("v201809.0123")
    >>> rewritten_datas = iter_rewritten(version_pattern, file_patterns, new_vinfo)
    >>> rfd = list(rewritten_datas)[0]
    >>> expected = [
    ...     '# This file is part of the pycalver project',
    ...     '# https://github.com/mbarkhau/pycalver',
    ...     '#',
    ...     '# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License',
    ...     '# SPDX-License-Identifier: MIT',
    ...     '"""PyCalVer: CalVer for Python Packages."""',
    ...     '',
    ...     '__version__ = "v201809.0123"',
    ...     '',
    ... ]
    >>> assert rfd.new_lines == expected
    '''

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
    r"""Generate diffs of rewritten files.

    >>> old_vinfo = v1version.parse_version_info("v201809.0123")
    >>> new_vinfo = v1version.parse_version_info("v201810.1124")
    >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    >>> diff_str = diff(old_vinfo, new_vinfo, file_patterns)
    >>> lines = diff_str.split("\n")
    >>> lines[:2]
    ['--- src/pycalver/__init__.py', '+++ src/pycalver/__init__.py']
    >>> assert lines[6].startswith('-__version__ = "v2')
    >>> assert not lines[6].startswith('-__version__ = "v201809.0123"')
    >>> lines[7]
    '+__version__ = "v201809.0123"'

    >>> file_patterns = {"LICENSE": ['Copyright (c) 2018-{year}']}
    >>> diff_str = diff(old_vinfo, new_vinfo, file_patterns)
    >>> assert not diff_str
    """

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
            errmsg = f"No patterns matched for '{file_path}'"
            raise rewrite.NoPatternMatch(errmsg)

        rfd   = rfd._replace(path=str(file_path))
        lines = rewrite.diff_lines(rfd)
        if len(lines) == 0 and has_updated_version:
            errmsg = f"No patterns matched for '{file_path}'"
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
