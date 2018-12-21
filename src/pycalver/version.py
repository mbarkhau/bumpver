# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
"""Functions related to version string manipulation.

>>> version_info = PYCALVER_RE.match("v201712.0123-alpha").groupdict()
>>> assert version_info == {
...     "version"     : "v201712.0123-alpha",
...     "calver"      : "v201712",
...     "year"        : "2017",
...     "month"       : "12",
...     "build"       : ".0123",
...     "build_no"    : "0123",
...     "release"     : "-alpha",
...     "release_tag" : "alpha",
... }
>>>
>>> version_info = PYCALVER_RE.match("v201712.0033").groupdict()
>>> assert version_info == {
...     "version"    : "v201712.0033",
...     "calver"     : "v201712",
...     "year"       : "2017",
...     "month"      : "12",
...     "build"      : ".0033",
...     "build_no"   : "0033",
...     "release"    : None,
...     "release_tag": None,
... }
"""

import re
import logging
import pkg_resources
import typing as typ
import datetime as dt

from . import lex_id

log = logging.getLogger("pycalver.version")


# https://regex101.com/r/fnj60p/10
PYCALVER_PATTERN = r"""
\b
(?P<version>
    (?P<calver>
       v                        # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?P<build>
        \.                      # "." build nr prefix
        (?P<build_no>\d{4,})
    )
    (?P<release>
        \-                      # "-" release prefix
        (?P<release_tag>alpha|beta|dev|rc|post)
    )?
)(?:\s|$)
"""

PYCALVER_RE: typ.Pattern[str] = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)


class VersionInfo(typ.NamedTuple):
    """Container for parsed version string."""

    version       : str
    pep440_version: str
    calver        : str
    year          : str
    month         : str
    build         : str
    build_no      : str
    release       : typ.Optional[str]
    release_tag   : typ.Optional[str]


def parse_version_info(version_str: str) -> VersionInfo:
    """Parse a PyCalVer string.

    >>> vnfo = parse_version_info("v201712.0033-beta")
    >>> assert vnfo == VersionInfo(
    ...     version       ="v201712.0033-beta",
    ...     pep440_version="201712.33b0",
    ...     calver        ="v201712",
    ...     year          ="2017",
    ...     month         ="12",
    ...     build         =".0033",
    ...     build_no      ="0033",
    ...     release       ="-beta",
    ...     release_tag   ="beta",
    ... )
    """
    match = PYCALVER_RE.match(version_str)
    if match is None:
        raise ValueError(f"Invalid PyCalVer string: {version_str}")

    kwargs = match.groupdict()
    kwargs['pep440_version'] = pycalver_to_pep440(kwargs['version'])
    return VersionInfo(**kwargs)


def current_calver() -> str:
    """Generate calver version string based on current date.

    example result: "v201812"
    """
    return dt.date.today().strftime("v%Y%m")


def incr(old_version: str, *, release: str = None) -> str:
    """Increment a full PyCalVer version string.

    Old_version is assumed to be a valid calver string,
    already validated in pycalver.config.parse.
    """
    old_ver = parse_version_info(old_version)

    new_calver = current_calver()

    if old_ver.calver > new_calver:
        log.warning(
            f"'version.incr' called with '{old_version}', "
            + f"which is from the future, "
            + f"maybe your system clock is out of sync."
        )
        # leave calver as is (don't go back in time)
        new_calver = old_ver.calver

    new_build = lex_id.next_id(old_ver.build[1:])
    new_release: typ.Optional[str] = None

    if release is None:
        if old_ver.release:
            # preserve existing release
            new_release = old_ver.release[1:]
        else:
            new_release = None
    elif release == 'final':
        new_release = None
    else:
        new_release = release

    new_version = new_calver + "." + new_build
    if new_release:
        new_version += "-" + new_release
    return new_version


def pycalver_to_pep440(version: str) -> str:
    """Derive pep440 compliant version string from PyCalVer version string.

    >>> pycalver_to_pep440("v201811.0007-beta")
    '201811.7b0'
    """
    return str(pkg_resources.parse_version(version))
