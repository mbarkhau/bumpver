# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Compose Regular Expressions from Patterns.

>>> pattern = compile_pattern("vYYYY0M.BUILD[-TAG]")
>>> version_info = pattern.regexp.match("v201712.0123-alpha")
>>> assert version_info.groupdict() == {
...     "year_y" : "2017",
...     "month"  : "12",
...     "bid"    : "0123",
...     "tag"    : "alpha",
... }
>>>
>>> version_info = pattern.regexp.match("201712.1234")
>>> assert version_info is None

>>> version_info = pattern.regexp.match("v201713.1234")
>>> assert version_info is None

>>> version_info = pattern.regexp.match("v201712.1234")
>>> assert version_info.groupdict() == {
...     "year_y" : "2017",
...     "month"  : "12",
...     "bid"    : "1234",
...     "tag"    : None,
... }
"""

import re
import typing as typ
import collections

from . import utils
from .patterns import RE_PATTERN_ESCAPES
from .patterns import Pattern

# NOTE (mb 2020-09-17): For patterns with different options '(AAA|BB|C)', the
#   patterns with more digits should be first/left of those with fewer digits:
#
#       good: (?:1[0-2]|[1-9])
#       bad:  (?:[1-9]|1[0-2])
#
#   This ensures that the longest match is done for a pattern.
#
#   This implies that patterns for smaller numbers sometimes must be right of
#   those for larger numbers. To be consistent we use this ordering not
#   sometimes but always (even though in theory it wouldn't matter):
#
#       good: (?:3[0-1]|[1-2][0-9]|[1-9])
#       bad:  (?:[1-2][0-9]|3[0-1]|[1-9])


PART_PATTERNS = collections.OrderedDict(
    [
        # Based on calver.org
        ('YYYY', r"[1-9][0-9]{3}"),
        ('YY'  , r"[1-9][0-9]?"),
        ('0Y'  , r"[0-9]{2}"),
        ('GGGG', r"[1-9][0-9]{3}"),
        ('GG'  , r"[1-9][0-9]?"),
        ('0G'  , r"[0-9]{2}"),
        ('Q'   , r"[1-4]"),
        ('MM'  , r"1[0-2]|[1-9]"),
        ('0M'  , r"1[0-2]|0[1-9]"),
        ('DD'  , r"3[0-1]|[1-2][0-9]|[1-9]"),
        ('0D'  , r"3[0-1]|[1-2][0-9]|0[1-9]"),
        ('JJJ' , r"36[0-6]|3[0-5][0-9]|[1-2][0-9][0-9]|[1-9][0-9]|[1-9]"),
        ('00J' , r"36[0-6]|3[0-5][0-9]|[1-2][0-9][0-9]|0[1-9][0-9]|00[1-9]"),
        # week numbering parts
        ('WW', r"5[0-2]|[1-4][0-9]|[0-9]"),
        ('0W', r"5[0-2]|[0-4][0-9]"),
        ('UU', r"5[0-2]|[1-4][0-9]|[0-9]"),
        ('0U', r"5[0-2]|[0-4][0-9]"),
        ('VV', r"5[0-3]|[1-4][0-9]|[1-9]"),
        ('0V', r"5[0-3]|[1-4][0-9]|0[1-9]"),
        # non calver parts
        ('MAJOR'  , r"[0-9]+"),
        ('MINOR'  , r"[0-9]+"),
        ('PATCH'  , r"[0-9]+"),
        ('BUILD'  , r"[0-9]+"),
        ('BLD'    , r"[1-9][0-9]*"),
        ('TAG'    , r"preview|final|alpha|beta|post|rc"),
        ('PYTAG'  , r"post|rc|a|b"),
        ('GITHASH', r"\.[0-9]+\+.*"),
        ('NUM'    , r"[0-9]+"),
        ('INC0'   , r"[0-9]+"),
        ('INC1'   , r"[1-9][0-9]*"),
    ]
)


PATTERN_PART_FIELDS = {
    'YYYY'   : 'year_y',
    'YY'     : 'year_y',
    '0Y'     : 'year_y',
    'GGGG'   : 'year_g',
    'GG'     : 'year_g',
    '0G'     : 'year_g',
    'Q'      : 'quarter',
    'MM'     : 'month',
    '0M'     : 'month',
    'DD'     : 'dom',
    '0D'     : 'dom',
    'JJJ'    : 'doy',
    '00J'    : 'doy',
    'MAJOR'  : 'major',
    'MINOR'  : 'minor',
    'PATCH'  : 'patch',
    'BUILD'  : 'bid',
    'BLD'    : 'bid',
    'TAG'    : 'tag',
    'PYTAG'  : 'pytag',
    'GITHASH': 'githash',
    'NUM'    : 'num',
    'INC0'   : 'inc0',
    'INC1'   : 'inc1',
    'WW'     : 'week_w',
    '0W'     : 'week_w',
    'UU'     : 'week_u',
    '0U'     : 'week_u',
    'VV'     : 'week_v',
    '0V'     : 'week_v',
}


PEP440_PART_SUBSTITUTIONS = {
    '0W'   : "WW",
    '0U'   : "UU",
    '0V'   : "VV",
    '0M'   : "MM",
    '0D'   : "DD",
    '00J'  : "JJJ",
    'BUILD': "BLD",
    'TAG'  : "PYTAG",
}


FieldValue = typ.Union[str, int]


def _fmt_num(val: FieldValue) -> str:
    return str(val)


def _fmt_bld(val: FieldValue) -> str:
    return str(int(val))


def _fmt_yy(year_y: FieldValue) -> str:
    return str(int(str(year_y)[-2:]))


def _fmt_0y(year_y: FieldValue) -> str:
    return f"{int(str(year_y)[-2:]):02}"


def _fmt_gg(year_g: FieldValue) -> str:
    return str(int(str(year_g)[-2:]))


def _fmt_0g(year_g: FieldValue) -> str:
    return f"{int(str(year_g)[-2:]):02}"


def _fmt_0m(month: FieldValue) -> str:
    return f"{int(month):02}"


def _fmt_0d(dom: FieldValue) -> str:
    return f"{int(dom):02}"


def _fmt_00j(doy: FieldValue) -> str:
    return f"{int(doy):03}"


def _fmt_0w(week_w: FieldValue) -> str:
    return f"{int(week_w):02}"


def _fmt_0u(week_u: FieldValue) -> str:
    return f"{int(week_u):02}"


def _fmt_0v(week_v: FieldValue) -> str:
    return f"{int(week_v):02}"


FormatterFunc = typ.Callable[[FieldValue], str]


PART_FORMATS: typ.Dict[str, FormatterFunc] = {
    'YYYY'   : _fmt_num,
    'YY'     : _fmt_yy,
    '0Y'     : _fmt_0y,
    'GGGG'   : _fmt_num,
    'GG'     : _fmt_gg,
    '0G'     : _fmt_0g,
    'Q'      : _fmt_num,
    'MM'     : _fmt_num,
    '0M'     : _fmt_0m,
    'DD'     : _fmt_num,
    '0D'     : _fmt_0d,
    'JJJ'    : _fmt_num,
    '00J'    : _fmt_00j,
    'MAJOR'  : _fmt_num,
    'MINOR'  : _fmt_num,
    'PATCH'  : _fmt_num,
    'BUILD'  : _fmt_num,
    'BLD'    : _fmt_bld,
    'TAG'    : _fmt_num,
    'PYTAG'  : _fmt_num,
    'GITHASH': _fmt_num,
    'NUM'    : _fmt_num,
    'INC0'   : _fmt_num,
    'INC1'   : _fmt_num,
    'WW'     : _fmt_num,
    '0W'     : _fmt_0w,
    'UU'     : _fmt_num,
    '0U'     : _fmt_0u,
    'VV'     : _fmt_num,
    '0V'     : _fmt_0v,
}


def _convert_to_pep440(version_pattern: str) -> str:
    # NOTE (mb 2020-09-20): This does not support some
    #   corner cases as specified in PEP440, in particular
    #   related to post and dev releases.

    pep440_pattern = version_pattern

    if pep440_pattern.startswith("v"):
        pep440_pattern = pep440_pattern[1:]

    pep440_pattern = pep440_pattern.replace(r"\[", "")
    pep440_pattern = pep440_pattern.replace(r"\]", "")

    pep440_pattern, _ = re.subn(r"[^a-zA-Z0-9\.\[\]]", "", pep440_pattern)

    part_names = list(PATTERN_PART_FIELDS.keys())
    part_names.sort(key=len, reverse=True)

    for part_name in part_names:
        if part_name not in version_pattern:
            continue
        if part_name not in PEP440_PART_SUBSTITUTIONS:
            continue

        substitution = PEP440_PART_SUBSTITUTIONS[part_name]
        if substitution in pep440_pattern:
            continue

        is_numerical_part = part_name not in ('TAG', 'PYTAG')
        if is_numerical_part:
            part_index              = pep440_pattern.find(part_name)
            is_zero_truncation_part = part_index == 0 or pep440_pattern[part_index - 1] == "."
            if is_zero_truncation_part:
                pep440_pattern = pep440_pattern.replace(part_name, substitution)
        else:
            pep440_pattern = pep440_pattern.replace(part_name, substitution)

    # PYTAG and NUM must be adjacent and also be the last (optional) part
    if 'PYTAGNUM' not in pep440_pattern:
        pep440_pattern = pep440_pattern.replace("PYTAG", "")
        pep440_pattern = pep440_pattern.replace("NUM"  , "")
        pep440_pattern = pep440_pattern.replace("[]"   , "")
        pep440_pattern += "[PYTAGNUM]"

    return pep440_pattern


def normalize_pattern(version_pattern: str, raw_pattern: str) -> str:
    normalized_pattern = raw_pattern
    if "{version}" in raw_pattern:
        normalized_pattern = normalized_pattern.replace("{version}", version_pattern)

    if "{pep440_version}" in normalized_pattern:
        pep440_version_pattern = _convert_to_pep440(version_pattern)
        normalized_pattern     = normalized_pattern.replace("{pep440_version}", pep440_version_pattern)

    return normalized_pattern


SortKey         = typ.Tuple[int, int]
PostitionedPart = typ.Tuple[int, int, str]


def _iter_part_patterns(pattern: str) -> typ.Iterator[typ.Tuple[SortKey, PostitionedPart]]:
    used_fields: typ.Set[str] = set()
    for part_name, part_pattern in PART_PATTERNS.items():
        end_idx = 0
        while True:
            start_idx = pattern.find(part_name, end_idx)
            if start_idx < 0:
                break

            field = PATTERN_PART_FIELDS[part_name]
            if field in used_fields:
                named_part_pattern = f"(?P<{field}_{len(used_fields)}>{part_pattern})"
            else:
                named_part_pattern = f"(?P<{field}>{part_pattern})"
            used_fields.add(field)

            end_idx         = start_idx + len(part_name)
            sort_key        = (-end_idx, -len(part_name))
            positioned_part = (start_idx, end_idx, named_part_pattern)
            yield (sort_key, positioned_part)


def _replace_pattern_parts(pattern: str) -> str:
    # The pattern is escaped, so that everything besides the format
    # string variables is treated literally.
    while True:
        new_pattern, _n = re.subn(r"([^\\]|^)\[", r"\1(?:", pattern)
        new_pattern, _m = re.subn(r"([^\\]|^)\]", r"\1)?" , new_pattern)
        pattern = new_pattern
        if _n + _m == 0:
            break

    part_patterns_by_index: typ.Dict[SortKey, PostitionedPart] = dict(_iter_part_patterns(pattern))

    # NOTE (mb 2020-09-17): The sorting is done so that we process items:
    #   - right before left
    #   - longer before shorter
    last_start_idx = len(pattern) + 1
    result_pattern = pattern
    for _, (start_idx, end_idx, named_part_pattern) in sorted(part_patterns_by_index.items()):
        if end_idx <= last_start_idx:
            result_pattern = (
                result_pattern[:start_idx] + named_part_pattern + result_pattern[end_idx:]
            )
            last_start_idx = start_idx

    return result_pattern


def _compile_pattern_re(normalized_pattern: str) -> typ.Pattern[str]:
    escaped_pattern = normalized_pattern
    for char, escaped in RE_PATTERN_ESCAPES:
        # [] braces are used for optional parts, such as [-TAG]/[-beta]
        # and need to be escaped manually.
        is_semantic_char = char in "[]\\"
        if not is_semantic_char:
            # escape it so it is a literal in the re pattern
            escaped_pattern = escaped_pattern.replace(char, escaped)

    pattern_str = _replace_pattern_parts(escaped_pattern)
    return re.compile(pattern_str)


@utils.memo
def compile_pattern(version_pattern: str, raw_pattern: typ.Optional[str] = None) -> Pattern:
    _raw_pattern       = version_pattern if raw_pattern is None else raw_pattern
    normalized_pattern = normalize_pattern(version_pattern, _raw_pattern)
    regexp             = _compile_pattern_re(normalized_pattern)
    return Pattern(version_pattern, normalized_pattern, regexp)


def compile_patterns(version_pattern: str, raw_patterns: typ.List[str]) -> typ.List[Pattern]:
    return [compile_pattern(version_pattern, raw_pattern) for raw_pattern in raw_patterns]
