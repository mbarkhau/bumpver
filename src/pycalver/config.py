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


def parse(config_file="setup.cfg") -> typ.Optional[typ.Dict[str, typ.Any]]:
    if not os.path.exists(config_file):
        log.error("File not found: setup.cfg")
        return None

    cfg_parser = configparser.RawConfigParser("")
    with io.open(config_file, mode="rt", encoding="utf-8") as fh:
        cfg_parser.readfp(fh)

    if "pycalver" not in cfg_parser:
        log.error("setup.cfg does not contain a [pycalver] section.")
        return None

    cfg = dict(cfg_parser.items("pycalver"))

    if "current_version" not in cfg:
        log.error("setup.cfg does not have 'pycalver.current_version'")
        return None

    current_version = cfg["current_version"]
    if PYCALVER_RE.match(current_version) is None:
        log.error(f"setup.cfg 'pycalver.current_version is invalid")
        log.error(f"current_version = {current_version}")
        return None

    cfg["pep440_version"] = str(pkg_resources.parse_version(current_version))

    cfg["tag"] = cfg.get("tag", "").lower() in ("yes", "true", "1", "on")
    cfg["commit"] = cfg.get("commit", "").lower() in ("yes", "true", "1", "on")

    cfg["file_patterns"] = {}

    for section_name in cfg_parser.sections():
        if not section_name.startswith("pycalver:file:"):
            continue

        filepath = section_name.split(":", 2)[-1]
        if not os.path.exists(filepath):
            log.error(f"No such file: {filepath} from {section_name} in setup.cfg")
            return None

        section = dict(cfg_parser.items(section_name))

        if "patterns" in section:
            cfg["file_patterns"][filepath] = [
                line.strip()
                for line in section["patterns"].splitlines()
                if line.strip()
            ]
        else:
            cfg["file_patterns"][filepath] = ["{version}", "{pep440_version}"]

    if not cfg["file_patterns"]:
        cfg["file_patterns"]["setup.cfg"] = ["{version}", "{pep440_version}"]

    log.debug(f"Config Parsed: {cfg}")

    return cfg


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
