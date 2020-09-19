import typing as typ


class Pattern(typ.NamedTuple):

    version_pattern: str  # "{pycalver}", "{year}.{month}", "vYYYY0M.BUILD"
    raw_pattern    : str  # '__version__ = "{version}"', "Copyright (c) YYYY"
    regexp         : typ.Pattern[str]


RE_PATTERN_ESCAPES = [
    ("\u005c", "\u005c\u005c"),
    ("-"     , "\u005c-"),
    ("."     , "\u005c."),
    ("+"     , "\u005c+"),
    ("*"     , "\u005c*"),
    ("?"     , "\u005c?"),
    ("{"     , "\u005c{"),
    ("}"     , "\u005c}"),
    ("["     , "\u005c["),
    ("]"     , "\u005c]"),
    ("("     , "\u005c("),
    (")"     , "\u005c)"),
]
