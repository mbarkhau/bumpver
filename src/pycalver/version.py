# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import logging
import datetime as dt

from . import lex_id
from . import parse

log = logging.getLogger("pycalver.version")


def current_calver() -> str:
    return dt.datetime.utcnow().strftime("v%Y%m")


def bump(old_version: str, release: str=None) -> str:
    # old_version is assumed to be a valid calver string,
    # validated in pycalver.config.parse.
    old_ver = parse.parse_version_info(old_version)

    new_calver = current_calver()
    new_build = lex_id.next_id(old_ver.build[1:])
    if release is None:
        if old_ver.release:
            # preserve existing release
            new_release = old_ver.release[1:]
        else:
            new_release = None
    else:
        new_release = release

    new_version = new_calver + "." + new_build
    if new_release:
        new_version += "-" + new_release
    return new_version


def incr_version(old_version: str, *, tag: str="__sentinel__") -> str:
    maybe_match: MaybeMatch = VERSION_RE.search(old_version)

    if maybe_match is None:
        raise ValueError(f"Invalid version string: {old_version}")

    prev_version_info: PyCalVerInfo = maybe_match.groupdict()

    prev_calver: str = prev_version_info["calver"]
    next_calver: str = current_calver()

    prev_build: str = prev_version_info["build"]
    if prev_calver > next_calver:
        log.warning(
            f"'incr_version' called with '{old_version}', " +
            f"which is from the future, " +
            f"maybe your system clock is out of sync."
        )
        next_calver = prev_calver   # leave calver as is

    next_build = lex_id.next_id(prev_build)
    new_version = f"{next_calver}.{next_build}"
    if tag != "__sentinel__":
        if tag is None:
            pass    # tag explicitly ignored/removed
        else:
            new_version += "-" + tag
    elif "tag" in prev_version_info:
        # preserve previous tag
        new_version += "-" + prev_version_info["tag"]

    assert old_version < new_version, f"{old_version}  {new_version}"
    return new_version
