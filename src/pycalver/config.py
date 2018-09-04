# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import io
import os
import configparser
import pkg_resources
import typing as typ
import datetime as dt

import logging

from .parse import PYCALVER_RE

log = logging.getLogger("pycalver.config")


class Config(typ.NamedTuple):

    current_version : str
    pep440_version  : str

    tag             : bool
    commit          : bool

    file_patterns   : typ.Dict[str, typ.List[str]]


MaybeConfig = typ.Optional[Config]


def parse_buffer(cfg_buffer: io.StringIO) -> MaybeConfig:
    cfg_parser = configparser.RawConfigParser()
    cfg_parser.readfp(cfg_buffer)

    if "pycalver" not in cfg_parser:
        log.error("setup.cfg does not contain a [pycalver] section.")
        return None

    base_cfg = dict(cfg_parser.items("pycalver"))

    if "current_version" not in base_cfg:
        log.error("setup.cfg does not have 'pycalver.current_version'")
        return None

    current_version = base_cfg["current_version"]
    if PYCALVER_RE.match(current_version) is None:
        log.error(f"setup.cfg 'pycalver.current_version is invalid")
        log.error(f"current_version = {current_version}")
        return None

    pep440_version = str(pkg_resources.parse_version(current_version))

    tag = base_cfg.get("tag", "").lower() in ("yes", "true", "1", "on")
    commit = base_cfg.get("commit", "").lower() in ("yes", "true", "1", "on")

    file_patterns: typ.Dict[str, typ.List[str]] = {}

    section_name: str
    for section_name in cfg_parser.sections():
        if not section_name.startswith("pycalver:file:"):
            continue

        filepath = section_name.split(":", 2)[-1]
        if not os.path.exists(filepath):
            log.error(f"No such file: {filepath} from {section_name} in setup.cfg")
            return None

        section: typ.Dict[str, str] = dict(cfg_parser.items(section_name))
        patterns = section.get("patterns")

        if patterns is None:
            file_patterns[filepath] = ["{version}", "{pep440_version}"]
        else:
            file_patterns[filepath] = [
                line.strip()
                for line in patterns.splitlines()
                if line.strip()
            ]

    if not file_patterns:
        file_patterns["setup.cfg"] = ["{version}", "{pep440_version}"]

    cfg = Config(current_version, pep440_version, tag, commit, file_patterns)
    log.debug(f"Config Parsed: {cfg}")
    return cfg


def parse(config_file="setup.cfg") -> MaybeConfig:
    if not os.path.exists(config_file):
        log.error("File not found: setup.cfg")
        return None

    cfg_buffer = io.StringIO()
    with io.open(config_file, mode="rt", encoding="utf-8") as fh:
        cfg_buffer.write(fh.read())

    cfg_buffer.seek(0)
    return parse_buffer(cfg_buffer)


def default_config_lines() -> typ.List[str]:
    initial_version = dt.datetime.now().strftime("v%Y%m.0001-dev")

    cfg_lines = [
        "[pycalver]",
        f"current_version = {initial_version}",
        "commit = True",
        "tag = True",
        "",
        "[pycalver:file:setup.cfg]",
        "patterns = ",
        "    current_version = {version}",
        "",
    ]

    if os.path.exists("setup.py"):
        cfg_lines.extend([
            "[pycalver:file:setup.py]",
            "patterns = ",
            "    \"{version}\"",
            "    \"{pep440_version}\"",
            "",
        ])

    if os.path.exists("README.rst"):
        cfg_lines.extend([
            "[pycalver:file:README.rst]",
            "patterns = ",
            "    {version}",
            "    {pep440_version}",
            "",
        ])

    if os.path.exists("README.md"):
        cfg_lines.extend([
            "[pycalver:file:README.md]",
            "    {version}",
            "    {pep440_version}",
            "",
        ])

    return cfg_lines
