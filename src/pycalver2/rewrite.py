# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Rewrite files, updating occurences of version strings."""

import io
import typing as typ
import logging

import pycalver2.version as v2version
import pycalver2.patterns as v2patterns
from pycalver import parse
from pycalver import config
from pycalver import rewrite as v1rewrite

logger = logging.getLogger("pycalver2.rewrite")


def rewrite_lines(
    pattern_strs: typ.List[str],
    new_vinfo   : v2version.VersionInfo,
    old_lines   : typ.List[str],
) -> typ.List[str]:
    # TODO reenable doctest
    # """Replace occurances of pattern_strs in old_lines with new_vinfo.

    # >>> new_vinfo = version.parse_version_info("v201811.0123-beta")
    # >>> pattern_strs = ['__version__ = "{pycalver}"']
    # >>> rewrite_lines(pattern_strs, new_vinfo, ['__version__ = "v201809.0002-beta"'])
    # ['__version__ = "v201811.0123-beta"']

    # >>> pattern_strs = ['__version__ = "{pep440_version}"']
    # >>> rewrite_lines(pattern_strs, new_vinfo, ['__version__ = "201809.2b0"'])
    # ['__version__ = "201811.123b0"']
    # """
    new_lines      = old_lines[:]
    found_patterns = set()

    patterns = [v2patterns.compile_pattern(p) for p in pattern_strs]
    matches  = parse.iter_matches(old_lines, patterns)
    for match in matches:
        found_patterns.add(match.pattern.raw)
        replacement = v2version.format_version(new_vinfo, match.pattern.raw)
        span_l, span_r = match.span
        new_line = match.line[:span_l] + replacement + match.line[span_r:]
        new_lines[match.lineno] = new_line

    non_matched_patterns = set(pattern_strs) - found_patterns
    if non_matched_patterns:
        for non_matched_pattern in non_matched_patterns:
            logger.error(f"No match for pattern '{non_matched_pattern}'")
            compiled_pattern_str = v2patterns.compile_pattern_str(non_matched_pattern)
            logger.error(f"Pattern compiles to regex '{compiled_pattern_str}'")
        raise v1rewrite.NoPatternMatch("Invalid pattern(s)")
    else:
        return new_lines


def rfd_from_content(
    pattern_strs: typ.List[str],
    new_vinfo   : v2version.VersionInfo,
    content     : str,
) -> v1rewrite.RewrittenFileData:
    # TODO reenable doctest
    # r"""Rewrite pattern occurrences with version string.

    # >>> new_vinfo = version.parse_version_info("v201809.0123")
    # >>> pattern_strs = ['__version__ = "{pycalver}"']
    # >>> content = '__version__ = "v201809.0001-alpha"'
    # >>> rfd = rfd_from_content(pattern_strs, new_vinfo, content)
    # >>> rfd.new_lines
    # ['__version__ = "v201809.0123"']
    # >>>
    # >>> new_vinfo = version.parse_version_info("v1.2.3", "v{semver}")
    # >>> pattern_strs = ['__version__ = "v{semver}"']
    # >>> content = '__version__ = "v1.2.2"'
    # >>> rfd = rfd_from_content(pattern_strs, new_vinfo, content)
    # >>> rfd.new_lines
    # ['__version__ = "v1.2.3"']
    # """
    line_sep  = v1rewrite.detect_line_sep(content)
    old_lines = content.split(line_sep)
    new_lines = rewrite_lines(pattern_strs, new_vinfo, old_lines)
    return v1rewrite.RewrittenFileData("<path>", line_sep, old_lines, new_lines)


def iter_rewritten(
    file_patterns: config.PatternsByGlob,
    new_vinfo    : v2version.VersionInfo,
) -> typ.Iterable[v1rewrite.RewrittenFileData]:
    # TODO reenable doctest
    # r'''Iterate over files with version string replaced.

    # >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    # >>> new_vinfo = version.parse_version_info("v201809.0123")
    # >>> rewritten_datas = iter_rewritten(file_patterns, new_vinfo)
    # >>> rfd = list(rewritten_datas)[0]
    # >>> assert rfd.new_lines == [
    # ...     '# This file is part of the pycalver project',
    # ...     '# https://gitlab.com/mbarkhau/pycalver',
    # ...     '#',
    # ...     '# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License',
    # ...     '# SPDX-License-Identifier: MIT',
    # ...     '"""PyCalVer: CalVer for Python Packages."""',
    # ...     '',
    # ...     '__version__ = "v201809.0123"',
    # ...     '',
    # ... ]
    # >>>
    # '''

    fobj: typ.IO[str]

    for file_path, pattern_strs in v1rewrite.iter_file_paths(file_patterns):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        rfd = rfd_from_content(pattern_strs, new_vinfo, content)
        yield rfd._replace(path=str(file_path))


def diff(
    new_vinfo    : v2version.VersionInfo,
    file_patterns: config.PatternsByGlob,
) -> str:
    # TODO reenable doctest
    # r"""Generate diffs of rewritten files.

    # >>> new_vinfo = version.parse_version_info("v201809.0123")
    # >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    # >>> diff_str = diff(new_vinfo, file_patterns)
    # >>> lines = diff_str.split("\n")
    # >>> lines[:2]
    # ['--- src/pycalver/__init__.py', '+++ src/pycalver/__init__.py']
    # >>> assert lines[6].startswith('-__version__ = "v2')
    # >>> assert not lines[6].startswith('-__version__ = "v201809.0123"')
    # >>> lines[7]
    # '+__version__ = "v201809.0123"'
    # """

    full_diff = ""
    fobj: typ.IO[str]

    for file_path, pattern_strs in sorted(v1rewrite.iter_file_paths(file_patterns)):
        with file_path.open(mode="rt", encoding="utf-8") as fobj:
            content = fobj.read()

        try:
            rfd = rfd_from_content(pattern_strs, new_vinfo, content)
        except v1rewrite.NoPatternMatch:
            # pylint:disable=raise-missing-from  ; we support py2, so not an option
            errmsg = f"No patterns matched for '{file_path}'"
            raise v1rewrite.NoPatternMatch(errmsg)

        rfd   = rfd._replace(path=str(file_path))
        lines = v1rewrite.diff_lines(rfd)
        if len(lines) == 0:
            errmsg = f"No patterns matched for '{file_path}'"
            raise v1rewrite.NoPatternMatch(errmsg)

        full_diff += "\n".join(lines) + "\n"

    full_diff = full_diff.rstrip("\n")
    return full_diff


def rewrite(file_patterns: config.PatternsByGlob, new_vinfo: v2version.VersionInfo) -> None:
    """Rewrite project files, updating each with the new version."""
    fobj: typ.IO[str]

    for file_data in iter_rewritten(file_patterns, new_vinfo):
        new_content = file_data.line_sep.join(file_data.new_lines)
        with io.open(file_data.path, mode="wt", encoding="utf-8") as fobj:
            fobj.write(new_content)
