# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
"""Parsing code for setup.cfg or pycalver.cfg"""

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

    current_version: str

    tag   : bool
    commit: bool

    file_patterns: typ.Dict[str, typ.List[str]]

    def _debug_str(self) -> str:
        cfg_str_parts = [
            f"Config Parsed: Config(",
            f"current_version='{self.current_version}'",
            f"tag={self.tag}",
            f"commit={self.commit}",
            f"file_patterns={{",
        ]

        for filename, patterns in self.file_patterns.items():
            for pattern in patterns:
                cfg_str_parts.append(f"\n    '{filename}': '{pattern}'")

        cfg_str_parts += ["\n})"]
        return ", ".join(cfg_str_parts)

    @property
    def pep440_version(self) -> str:
        return str(pkg_resources.parse_version(self.current_version))


MaybeConfig = typ.Optional[Config]

FilePatterns = typ.Dict[str, typ.List[str]]


def _parse_file_patterns(
    cfg_parser: configparser.RawConfigParser, config_filename: str
) -> typ.Optional[FilePatterns]:

    file_patterns: FilePatterns = {}

    section_name: str
    for section_name in cfg_parser.sections():
        if not section_name.startswith("pycalver:file:"):
            continue

        filepath = section_name.split(":", 2)[-1]
        if not os.path.exists(filepath):
            log.error(f"No such file: {filepath} from {section_name} in {config_filename}")
            return None

        section: typ.Dict[str, str] = dict(cfg_parser.items(section_name))
        patterns = section.get("patterns")

        if patterns is None:
            file_patterns[filepath] = ["{version}", "{pep440_version}"]
        else:
            file_patterns[filepath] = [
                line.strip() for line in patterns.splitlines() if line.strip()
            ]

    if not file_patterns:
        file_patterns[f"{config_filename}"] = ["{version}", "{pep440_version}"]

    return file_patterns


def _parse_buffer(cfg_buffer: io.StringIO, config_filename: str = "<pycalver.cfg>") -> MaybeConfig:
    cfg_parser = configparser.RawConfigParser()

    if hasattr(cfg_parser, 'read_file'):
        cfg_parser.read_file(cfg_buffer)
    else:
        cfg_parser.readfp(cfg_buffer)

    if not cfg_parser.has_section("pycalver"):
        log.error(f"{config_filename} does not contain a [pycalver] section.")
        return None

    base_cfg = dict(cfg_parser.items("pycalver"))

    if "current_version" not in base_cfg:
        log.error(f"{config_filename} does not have 'pycalver.current_version'")
        return None

    current_version = base_cfg['current_version']

    if PYCALVER_RE.match(current_version) is None:
        log.error(f"{config_filename} 'pycalver.current_version is invalid")
        log.error(f"current_version = {current_version}")
        return None

    tag    = base_cfg.get("tag"   , "").lower() in ("yes", "true", "1", "on")
    commit = base_cfg.get("commit", "").lower() in ("yes", "true", "1", "on")

    file_patterns = _parse_file_patterns(cfg_parser, config_filename)

    if file_patterns is None:
        return None

    if tag and not commit:
        log.error(f"Invalid configuration in {config_filename}")
        log.error("     pycalver.commit = True required if pycalver.tag = True")
        return None

    cfg = Config(current_version, tag, commit, file_patterns)

    log.debug(cfg._debug_str())

    return cfg


def parse(config_filename: str = None) -> MaybeConfig:
    if config_filename is None:
        if os.path.exists("pycalver.cfg"):
            config_filename = "pycalver.cfg"
        elif os.path.exists("setup.cfg"):
            config_filename = "setup.cfg"
        else:
            log.error("File not found: pycalver.cfg or setup.cfg")
            return None

    if not os.path.exists(config_filename):
        log.error(f"File not found: {config_filename}")
        return None

    cfg_buffer = io.StringIO()
    with io.open(config_filename, mode="rt", encoding="utf-8") as fh:
        cfg_buffer.write(fh.read())

    cfg_buffer.seek(0)
    return _parse_buffer(cfg_buffer, config_filename)


DEFAULT_CONFIG_BASE_STR = """
[pycalver]
current_version = {initial_version}
commit = True
tag = True

[pycalver:file:setup.cfg]
patterns =
    current_version = {{version}}
"""


DEFAULT_CONFIG_SETUP_PY_STR = """
[pycalver:file:setup.py]
patterns =
    "{version}"
    "{pep440_version}"
"""


DEFAULT_CONFIG_README_RST_STR = """
[pycalver:file:README.rst]
patterns =
    {version}
    {pep440_version}
"""


DEFAULT_CONFIG_README_MD_STR = """
[pycalver:file:README.md]
patterns =
    {version}
    {pep440_version}
"""


def default_config_lines() -> typ.List[str]:
    initial_version = dt.datetime.now().strftime("v%Y%m.0001-dev")

    cfg_str = DEFAULT_CONFIG_BASE_STR.format(initial_version=initial_version)

    cfg_lines = cfg_str.splitlines()

    if os.path.exists("setup.py"):
        cfg_lines.extend(DEFAULT_CONFIG_SETUP_PY_STR.splitlines())

    if os.path.exists("README.rst"):
        cfg_lines.extend(DEFAULT_CONFIG_README_RST_STR.splitlines())

    if os.path.exists("README.md"):
        cfg_lines.extend(DEFAULT_CONFIG_README_MD_STR.splitlines())

    cfg_lines += [""]

    return cfg_lines
