import re
import textwrap

from . import pysix
from . import patterns


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


def regex101_url(pattern: patterns.Pattern) -> str:
    try:
        regex_text = format_regex(pattern.regexp.pattern)
    except re.error:
        regex_text = pattern.regexp.pattern

    return "".join(
        (
            "https://regex101.com/",
            "?flavor=python",
            "&flags=gmx" "&regex=" + pysix.quote(regex_text),
        )
    )
