# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import io
import difflib
import logging
import typing as typ

from . import parse

log = logging.getLogger("pycalver.rewrite")


def _detect_line_sep(content: str) -> str:
    if "\r\n" in content:
        return "\r\n"
    elif "\r" in content:
        return "\r"
    else:
        return "\n"


def rewrite_lines(
    old_lines: typ.List[str], patterns: typ.List[str], new_version: str
) -> typ.List[str]:
    new_version_nfo        = parse.parse_version_info(new_version)
    new_version_fmt_kwargs = new_version_nfo._asdict()

    new_lines = old_lines.copy()

    matches: typ.List[parse.PatternMatch] = parse.parse_patterns(old_lines, patterns)

    for m in matches:
        replacement = m.pattern.format(**new_version_fmt_kwargs)
        span_l, span_r = m.span
        new_line = m.line[:span_l] + replacement + m.line[span_r:]
        new_lines[m.lineno] = new_line

    return new_lines


def rewrite(
    new_version: str, file_patterns: typ.Dict[str, typ.List[str]], dry=False, verbose: int = 0
) -> None:
    for filepath, patterns in file_patterns.items():
        with io.open(filepath, mode="rt", encoding="utf-8") as fh:
            content = fh.read()

        line_sep  = _detect_line_sep(content)
        old_lines = content.split(line_sep)
        new_lines = rewrite_lines(old_lines, patterns, new_version)

        if dry or verbose:
            diff_lines = difflib.unified_diff(
                old_lines, new_lines, lineterm="", fromfile="a/" + filepath, tofile="b/" + filepath
            )
            print("\n".join(diff_lines))

        if dry:
            continue

        new_content = line_sep.join(new_lines)
        with io.open(filepath, mode="wt", encoding="utf-8") as fh:
            fh.write(new_content)
