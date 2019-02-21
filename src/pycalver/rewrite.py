# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT
"""Rewrite files, updating occurences of version strings."""

import io
import glob
import difflib
import logging
import typing as typ
import pathlib2 as pl

from . import parse
from . import config
from . import version


log = logging.getLogger("pycalver.rewrite")


def detect_line_sep(content: str) -> str:
    r"""Parse line separator from content.

    >>> detect_line_sep('\r\n')
    '\r\n'
    >>> detect_line_sep('\r')
    '\r'
    >>> detect_line_sep('\n')
    '\n'
    >>> detect_line_sep('')
    '\n'
    """
    if "\r\n" in content:
        return "\r\n"
    elif "\r" in content:
        return "\r"
    else:
        return "\n"


def rewrite_lines(
    patterns: typ.List[str], new_version: str, old_lines: typ.List[str]
) -> typ.List[str]:
    """Replace occurances of patterns in old_lines with new_version.

    >>> patterns = ['__version__ = "{pycalver}"']
    >>> rewrite_lines(patterns, "v201811.0123-beta", ['__version__ = "v201809.0002-beta"'])
    ['__version__ = "v201811.0123-beta"']

    >>> patterns = ['__version__ = "{pep440_version}"']
    >>> rewrite_lines(patterns, "v201811.0123-beta", ['__version__ = "201809.2b0"'])
    ['__version__ = "201811.123b0"']
    """
    new_version_nfo = version.parse_version_info(new_version)

    new_lines = old_lines[:]

    for m in parse.iter_matches(old_lines, patterns):
        replacement = version.format_version(new_version_nfo, m.pattern)
        span_l, span_r = m.span
        new_line = m.line[:span_l] + replacement + m.line[span_r:]
        new_lines[m.lineno] = new_line

    return new_lines


class RewrittenFileData(typ.NamedTuple):
    """Container for line-wise content of rewritten files."""

    path     : str
    line_sep : str
    old_lines: typ.List[str]
    new_lines: typ.List[str]


def rfd_from_content(patterns: typ.List[str], new_version: str, content: str) -> RewrittenFileData:
    r"""Rewrite pattern occurrences with version string.

    >>> patterns = ['__version__ = "{pycalver}"']
    >>> content = '__version__ = "v201809.0001-alpha"'
    >>> rfd = rfd_from_content(patterns, "v201809.0123", content)
    >>> rfd.new_lines
    ['__version__ = "v201809.0123"']
    """
    line_sep  = detect_line_sep(content)
    old_lines = content.split(line_sep)
    new_lines = rewrite_lines(patterns, new_version, old_lines)
    return RewrittenFileData("<path>", line_sep, old_lines, new_lines)


def _iter_file_paths(
    file_patterns: config.PatternsByGlob
) -> typ.Iterable[typ.Tuple[pl.Path, config.Patterns]]:
    for globstr, patterns in file_patterns.items():
        file_paths = glob.glob(globstr)
        if not any(file_paths):
            errmsg = f"No files found for path/glob '{globstr}'"
            raise ValueError(errmsg)
        for file_path_str in file_paths:
            file_path = pl.Path(file_path_str)
            yield (file_path, patterns)


def iter_rewritten(
    file_patterns: config.PatternsByGlob, new_version: str
) -> typ.Iterable[RewrittenFileData]:
    r'''Iterate over files with version string replaced.

    >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    >>> rewritten_datas = iter_rewritten(file_patterns, "v201809.0123")
    >>> rfd = list(rewritten_datas)[0]
    >>> assert rfd.new_lines == [
    ...     '# This file is part of the pycalver project',
    ...     '# https://gitlab.com/mbarkhau/pycalver',
    ...     '#',
    ...     '# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License',
    ...     '# SPDX-License-Identifier: MIT',
    ...     '"""PyCalVer: CalVer for Python Packages."""',
    ...     '',
    ...     '__version__ = "v201809.0123"',
    ...     '',
    ... ]
    >>>
    '''
    fh: typ.IO[str]

    for file_path, patterns in _iter_file_paths(file_patterns):
        with file_path.open(mode="rt", encoding="utf-8") as fh:
            content = fh.read()

        rfd = rfd_from_content(patterns, new_version, content)
        yield rfd._replace(path=str(file_path))


def diff_lines(rfd: RewrittenFileData) -> typ.List[str]:
    r"""Generate unified diff.

    >>> rfd = RewrittenFileData(
    ...    path      = "<path>",
    ...    line_sep  = "\n",
    ...    old_lines = ["foo"],
    ...    new_lines = ["bar"],
    ... )
    >>> diff_lines(rfd)
    ['--- <path>', '+++ <path>', '@@ -1 +1 @@', '-foo', '+bar']
    """
    lines = difflib.unified_diff(
        a=rfd.old_lines, b=rfd.new_lines, lineterm="", fromfile=rfd.path, tofile=rfd.path
    )
    return list(lines)


def diff(new_version: str, file_patterns: config.PatternsByGlob) -> str:
    r"""Generate diffs of rewritten files.

    >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{pycalver}"']}
    >>> diff_str = diff("v201809.0123", file_patterns)
    >>> lines = diff_str.split("\n")
    >>> lines[:2]
    ['--- src/pycalver/__init__.py', '+++ src/pycalver/__init__.py']
    >>> assert lines[6].startswith('-__version__ = "v2')
    >>> assert not lines[6].startswith('-__version__ = "v201809.0123"')
    >>> lines[7]
    '+__version__ = "v201809.0123"'
    """

    full_diff = ""
    fh: typ.IO[str]

    for file_path, patterns in sorted(_iter_file_paths(file_patterns)):
        with file_path.open(mode="rt", encoding="utf-8") as fh:
            content = fh.read()

        rfd = rfd_from_content(patterns, new_version, content)
        rfd = rfd._replace(path=str(file_path))
        lines = diff_lines(rfd)
        if len(lines) == 0:
            errmsg = f"No patterns matched for '{file_path}'"
            raise ValueError(errmsg)

        full_diff += "\n".join(lines) + "\n"

    full_diff = full_diff.rstrip("\n")
    return full_diff


def rewrite(new_version: str, file_patterns: config.PatternsByGlob) -> None:
    """Rewrite project files, updating each with the new version."""
    fh: typ.IO[str]

    for file_data in iter_rewritten(file_patterns, new_version):
        new_content = file_data.line_sep.join(file_data.new_lines)
        with io.open(file_data.path, mode="wt", encoding="utf-8") as fh:
            fh.write(new_content)
