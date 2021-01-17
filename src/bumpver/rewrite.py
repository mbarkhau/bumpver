# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import difflib

import pathlib2 as pl

from . import config
from .patterns import Pattern


class NoPatternMatch(Exception):
    """Pattern not found in content.

    logger.error is used to show error info about the patterns so
    that users can debug what is wrong with them. The class
    itself doesn't capture that info. This approach is used so
    that all patter issues can be shown, rather than bubbling
    all the way up the stack on the very first pattern with no
    matches.
    """


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


class RewrittenFileData(typ.NamedTuple):
    """Container for line-wise content of rewritten files."""

    path     : str
    line_sep : str
    old_lines: typ.List[str]
    new_lines: typ.List[str]


PathPatternsItem = typ.Tuple[pl.Path, typ.List[Pattern]]


def iter_path_patterns_items(
    file_patterns: config.PatternsByFile,
) -> typ.Iterable[PathPatternsItem]:
    for filepath_str, patterns in file_patterns.items():
        filepath_obj = pl.Path(filepath_str)
        if filepath_obj.exists():
            yield (filepath_obj, patterns)
        else:
            errmsg = f"File does not exist: '{filepath_str}'"
            raise IOError(errmsg)


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
        a=rfd.old_lines,
        b=rfd.new_lines,
        lineterm="",
        fromfile=rfd.path,
        tofile=rfd.path,
    )
    return list(lines)
