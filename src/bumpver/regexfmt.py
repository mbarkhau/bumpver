# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2023 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import re
import logging
import textwrap

from . import pysix

logger = logging.getLogger("bumpver.regexfmt")


def format_regex(regex: str) -> str:
    r"""Format a regex pattern suitible for flags=re.VERBOSE.

    >>> regex = r"\[CalVer v(?P<year_y>[1-9][0-9]{3})(?P<month>(?:1[0-2]|0[1-9]))"
    >>> print(format_regex(regex))
    \[CalVer[ ]v
    (?P<year_y>[1-9][0-9]{3})
    (?P<month>
        (?:1[0-2]|0[1-9])
    )
    """
    # provoke error for invalid regex
    re.compile(regex)

    tmp_regex = regex.replace(" ", r"[ ]")
    tmp_regex = tmp_regex.replace('"', r'\"')
    tmp_regex, _ = re.subn(r"([^\\])?\)(\?)?", "\\1)\\2\n", tmp_regex)
    tmp_regex, _ = re.subn(r"([^\\])\("      , "\\1\n("   , tmp_regex)
    tmp_regex, _ = re.subn(r"^\)\)"          , ")\n)"     , tmp_regex, flags=re.MULTILINE)
    lines          = tmp_regex.splitlines()
    indented_lines = []
    level          = 0
    for line in lines:
        if line.strip():
            increment = line.count("(") - line.count(")")
            if increment >= 0:
                line = "    " * level + line
                level += increment
            else:
                level += increment
                line = "    " * level + line
            indented_lines.append(line)

    formatted_regex = "\n".join(indented_lines)

    # provoke error if there is a bug in the formatting code
    re.compile(formatted_regex)
    return formatted_regex


def pyexpr_regex(regex: str) -> str:
    try:
        formatted_regex = format_regex(regex)
        formatted_regex = textwrap.indent(formatted_regex.rstrip(), "    ")
        return 're.compile(r"""\n' + formatted_regex + '\n""", flags=re.VERBOSE)'
    except re.error:
        return f"re.compile({repr(regex)})"


URL_TEMPLATE = "https://regex101.com/?flavor=python&flags=gmx&regex="


def regex101_url(regex_pattern: str) -> str:
    try:
        regex_pattern = format_regex(regex_pattern)
    except re.error:
        logger.warning(f"Error formatting regex '{repr(regex_pattern)}'")

    return URL_TEMPLATE + pysix.quote(regex_pattern)
