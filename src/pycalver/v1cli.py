#!/usr/bin/env python
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
CLI module for PyCalVer.

Provided subcommands: show, test, init, bump
"""
import typing as typ
import logging

from . import config
from . import version
from . import v1rewrite
from . import v1version

logger = logging.getLogger("pycalver.v1cli")


def update_cfg_from_vcs(cfg: config.Config, all_tags: typ.List[str]) -> config.Config:
    version_tags = [tag for tag in all_tags if v1version.is_valid(tag, cfg.version_pattern)]
    if not version_tags:
        logger.debug("no vcs tags found")
        return cfg

    version_tags.sort(reverse=True)
    _debug_tags = ", ".join(version_tags[:3])
    logger.debug(f"found tags: {_debug_tags} ... ({len(version_tags)} in total)")
    latest_version_tag    = version_tags[0]
    latest_version_pep440 = version.to_pep440(latest_version_tag)
    if latest_version_tag <= cfg.current_version:
        return cfg

    logger.info(f"Working dir version        : {cfg.current_version}")
    logger.info(f"Latest version from VCS tag: {latest_version_tag}")
    return cfg._replace(
        current_version=latest_version_tag,
        pep440_version=latest_version_pep440,
    )


def get_diff(cfg: config.Config, new_version: str) -> str:
    old_vinfo = v1version.parse_version_info(cfg.current_version, cfg.version_pattern)
    new_vinfo = v1version.parse_version_info(new_version        , cfg.version_pattern)
    return v1rewrite.diff(old_vinfo, new_vinfo, cfg.file_patterns)
