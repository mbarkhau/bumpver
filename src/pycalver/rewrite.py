# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT
"""Rewrite files, updating occurences of version strings."""

import io
import difflib
import logging
import typing as typ

from . import parse
from . import config

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

    >>> old_lines = ['__version__ = "v201809.0002-beta"']
    >>> patterns = ['__version__ = "{version}"']
    >>> new_lines = rewrite_lines(patterns, "v201811.0123-beta", old_lines)
    >>> assert new_lines == ['__version__ = "v201811.0123-beta"']
    """
    new_version_nfo        = parse.VersionInfo.parse(new_version)
    new_version_fmt_kwargs = new_version_nfo._asdict()

    new_lines = old_lines.copy()

    for m in parse.PatternMatch.iter_matches(old_lines, patterns):
        replacement = m.pattern.format(**new_version_fmt_kwargs)
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

    @property
    def diff_lines(self) -> typ.List[str]:
        r"""Generate unified diff.

        >>> rwd = RewrittenFileData(
        ...    path      = "<path>",
        ...    line_sep  = "\n",
        ...    old_lines = ["foo"],
        ...    new_lines = ["bar"],
        ... )
        >>> rwd.diff_lines
        ['--- <path>', '+++ <path>', '@@ -1 +1 @@', '-foo', '+bar']
        """
        return list(
            difflib.unified_diff(
                a=self.old_lines,
                b=self.new_lines,
                lineterm="",
                fromfile=self.path,
                tofile=self.path,
            )
        )

    @staticmethod
    def from_content(
        patterns: typ.List[str], new_version: str, content: str
    ) -> 'RewrittenFileData':
        r"""Rewrite pattern occurrences with version string.

        >>> patterns = ['__version__ = "{version}"']
        >>> content = '__version__ = "v201809.0001-alpha"'
        >>> rwd = RewrittenFileData.from_content(patterns, "v201809.0123", content)
        >>> assert rwd.new_lines == ['__version__ = "v201809.0123"']
        """
        line_sep  = detect_line_sep(content)
        old_lines = content.split(line_sep)
        new_lines = rewrite_lines(patterns, new_version, old_lines)
        return RewrittenFileData("<path>", line_sep, old_lines, new_lines)

    @staticmethod
    def iter_rewritten(
        file_patterns: config.PatternsByFilePath, new_version: str
    ) -> typ.Iterable['RewrittenFileData']:
        r'''Iterate over files with version string replaced.

        >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{version}"']}
        >>> rewritten_datas = RewrittenFileData.iter_rewritten(file_patterns, "v201809.0123")
        >>> rwd = list(rewritten_datas)[0]
        >>> assert rwd.new_lines == [
        ...     '# This file is part of the pycalver project',
        ...     '# https://gitlab.com/mbarkhau/pycalver',
        ...     '#',
        ...     '# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License',
        ...     '# SPDX-License-Identifier: MIT',
        ...     '"""PyCalVer: Automatic CalVer Versioning for Python Packages."""',
        ...     '',
        ...     '__version__ = "v201809.0123"',
        ...     '',
        ... ]
        >>>
        '''
        for filepath, patterns in file_patterns.items():
            with io.open(filepath, mode="rt", encoding="utf-8") as fh:
                content = fh.read()

            rfd = RewrittenFileData.from_content(patterns, new_version, content)
            yield rfd._replace(path=filepath)


def diff(new_version: str, file_patterns: config.PatternsByFilePath) -> str:
    r"""Generate diffs of rewritten files.

    >>> file_patterns = {"src/pycalver/__init__.py": ['__version__ = "{version}"']}
    >>> diff_lines = diff("v201809.0123", file_patterns).split("\n")
    >>> diff_lines[:2]
    ['--- src/pycalver/__init__.py', '+++ src/pycalver/__init__.py']
    >>> assert diff_lines[6].startswith('-__version__ = "v2')
    >>> assert not diff_lines[6].startswith('-__version__ = "v201809.0123"')
    >>> diff_lines[7]
    '+__version__ = "v201809.0123"'
    """
    diff_lines: typ.List[str] = []

    for rwd in RewrittenFileData.iter_rewritten(file_patterns, new_version):
        diff_lines += rwd.diff_lines

    return "\n".join(diff_lines)


def rewrite(new_version: str, file_patterns: config.PatternsByFilePath) -> None:
    """Rewrite project files, updating each with the new version."""

    for file_data in RewrittenFileData.iter_rewritten(file_patterns, new_version):
        new_content = file_data.line_sep.join(file_data.new_lines)
        with io.open(file_data.path, mode="wt", encoding="utf-8") as fh:
            fh.write(new_content)
