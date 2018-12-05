# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
"""Parse setup.cfg or pycalver.cfg files."""

import io
import os
import toml
import configparser
import typing as typ
import pathlib2 as pl
import datetime as dt

import logging

from .parse import PYCALVER_RE
from . import version

log = logging.getLogger("pycalver.config")

PatternsByFilePath = typ.Dict[str, typ.List[str]]


class ProjectContext(typ.NamedTuple):
    """Container class for project info."""

    path           : pl.Path
    config_filepath: pl.Path
    config_format  : str
    vcs_type       : typ.Optional[str]


def init_project_ctx(project_path: typ.Union[str, pl.Path, None] = ".") -> ProjectContext:
    """Initialize ProjectContext from a path."""
    if isinstance(project_path, str):
        path = pl.Path(project_path)
    else:
        path = project_path

    if (path / "pyproject.toml").exists():
        config_filepath = path / "pyproject.toml"
        config_format   = 'toml'
    if (path / "setup.cfg").exists():
        config_filepath = path / "setup.cfg"
        config_format   = 'cfg'
    else:
        config_filepath = path / "pycalver.toml"
        config_format   = 'toml'

    if (path / ".git").exists():
        vcs_type = 'git'
    elif (path / ".hg").exists():
        vcs_type = 'hg'
    else:
        vcs_type = None

    return ProjectContext(path, config_filepath, config_format, vcs_type)


RawConfig = typ.Dict[str, typ.Any]


class Config(typ.NamedTuple):
    """Container for parameters parsed from a config file."""

    current_version: str
    pep440_version : str

    tag   : bool
    commit: bool
    push: bool

    file_patterns: PatternsByFilePath


def _debug_str(cfg: Config) -> str:
    cfg_str_parts = [
        f"Config Parsed: Config(",
        f"current_version='{cfg.current_version}'",
        f"pep440_version='{cfg.pep440_version}'",
        f"tag={cfg.tag}",
        f"commit={cfg.commit}",
        f"push={cfg.push}",
        f"file_patterns={{",
    ]

    for filepath, patterns in cfg.file_patterns.items():
        for pattern in patterns:
            cfg_str_parts.append(f"\n    '{filepath}': '{pattern}'")

    cfg_str_parts += ["\n})"]
    return ", ".join(cfg_str_parts)


MaybeConfig = typ.Optional[Config]

FilePatterns = typ.Dict[str, typ.List[str]]


def _parse_cfg_file_patterns(
    cfg_parser: configparser.RawConfigParser,
) -> FilePatterns:

    file_patterns: FilePatterns = {}

    for filepath, patterns_str in cfg_parser.items("pycalver:file_patterns"):
        patterns: typ.List[str] = []
        for line in patterns_str.splitlines():
            pattern = line.strip()
            if pattern:
                patterns.append(pattern)

        file_patterns[filepath] = patterns

    return file_patterns


def _parse_cfg_option(option_name):
    # preserve uppercase filenames
    return option_name


def _parse_cfg(cfg_buffer: typ.TextIO) -> RawConfig:
    cfg_parser = configparser.RawConfigParser()
    cfg_parser.optionxform = _parse_cfg_option

    if hasattr(cfg_parser, 'read_file'):
        cfg_parser.read_file(cfg_buffer)
    else:
        cfg_parser.readfp(cfg_buffer)  # python2 compat

    if not cfg_parser.has_section("pycalver"):
        log.error("Missing [pycalver] section.")
        return None

    raw_cfg = dict(cfg_parser.items("pycalver"))

    raw_cfg['commit'] = raw_cfg.get('commit', False)
    raw_cfg['tag'   ] = raw_cfg.get('tag'   , None)
    raw_cfg['push'  ] = raw_cfg.get('push'  , None)

    if isinstance(raw_cfg['commit'], str):
        raw_cfg['commit'] = raw_cfg['commit'].lower() in ("yes", "true", "1", "on")
    if isinstance(raw_cfg['tag'], str):
        raw_cfg['tag'] = raw_cfg['tag'].lower() in ("yes", "true", "1", "on")
    if isinstance(raw_cfg['push'], str):
        raw_cfg['push'] = raw_cfg['push'].lower() in ("yes", "true", "1", "on")

    raw_cfg['file_patterns'] = _parse_cfg_file_patterns(cfg_parser)

    return raw_cfg


def _parse_toml(cfg_buffer: typ.TextIO) -> RawConfig:
    raw_full_cfg = toml.load(cfg_buffer)
    raw_cfg = raw_full_cfg.get('pycalver', {})

    raw_cfg['commit'] = raw_cfg.get('commit', False)
    raw_cfg['tag'   ] = raw_cfg.get('tag'   , None)
    raw_cfg['push'  ] = raw_cfg.get('push'  , None)

    return raw_cfg


def _parse_config(raw_cfg: RawConfig) -> Config:
    if 'current_version' not in raw_cfg:
        raise ValueError("Missing 'pycalver.current_version'")

    version_str = raw_cfg['current_version']
    version_str = raw_cfg['current_version'] = version_str.strip("'\" ")

    if PYCALVER_RE.match(version_str) is None:
        raise ValueError(f"Invalid current_version = {version_str}")

    pep440_version = version.pycalver_to_pep440(version_str)

    commit = raw_cfg['commit']
    tag    = raw_cfg['tag']
    push   = raw_cfg['push']

    if tag is None:
        tag = raw_cfg['tag'] = False
    if push is None:
        push = raw_cfg['push'] = False

    if tag and not commit:
        raise ValueError("pycalver.commit = true required if pycalver.tag = true")

    if push and not commit:
        raise ValueError("pycalver.commit = true required if pycalver.push = true")

    file_patterns = raw_cfg['file_patterns']

    for filepath in file_patterns.keys():
        if not os.path.exists(filepath):
            log.warning(f"Invalid configuration, no such file: {filepath}")

    cfg = Config(version_str, pep440_version, tag, commit, push, file_patterns)
    log.debug(_debug_str(cfg))
    return cfg


def parse(ctx: ProjectContext) -> MaybeConfig:
    """Parse config file if available."""
    if not ctx.config_filepath.exists():
        log.error(f"File not found: {ctx.config_filepath}")
        return None

    raw_cfg: typ.Optional[RawConfig]

    try:
        with ctx.config_filepath.open(mode="rt", encoding="utf-8") as fh:
            if ctx.config_format == 'toml':
                raw_cfg = _parse_toml(fh)
            elif ctx.config_format == 'cfg':
                raw_cfg = _parse_cfg(fh)
            else:
                return None

        return _parse_config(raw_cfg)
    except ValueError as ex:
        log.error(f"Error parsing {ctx.config_filepath}: {str(ex)}")
        return None


DEFAULT_CONFIGPARSER_BASE_STR = """
[pycalver]
current_version = "{initial_version}"
commit = True
tag = True
push = True
[pycalver:file_patterns]
"""


DEFAULT_CONFIGPARSER_SETUP_CFG_STR = """
setup.cfg =
    current_version = "{{version}}"
"""


DEFAULT_CONFIGPARSER_SETUP_PY_STR = """
setup.py =
    "{version}"
    "{pep440_version}"
"""


DEFAULT_CONFIGPARSER_README_RST_STR = """
README.rst =
    "{version}"
    "{pep440_version}"
"""


DEFAULT_CONFIGPARSER_README_MD_STR = """
README.md =
    "{version}"
    "{pep440_version}"
"""


DEFAULT_TOML_BASE_STR = """
[pycalver]
current_version = "{initial_version}"
commit = true
tag = true
push = true
[pycalver.file_patterns]
"""


DEFAULT_TOML_PYCALVER_STR = """
"pycalver.toml" = [
    'current_version = "{{version}}"',
]
"""


DEFAULT_TOML_PYPROJECT_STR = """
"pyproject.toml" = [
    'current_version = "{{version}}"',
]
"""


DEFAULT_TOML_SETUP_PY_STR = """
"setup.py" = [
    "{version}",
    "{pep440_version}",
]
"""


DEFAULT_TOML_README_RST_STR = """
"README.rst" = [
    "{version}",
    "{pep440_version}",
]
"""


DEFAULT_TOML_README_MD_STR = """
"README.md" = [
    "{version}",
    "{pep440_version}",
]
"""


def default_config(ctx: ProjectContext) -> str:
    """Generate initial default config."""
    if ctx.config_format == 'cfg':
        base_str = DEFAULT_CONFIGPARSER_BASE_STR

        default_pattern_strs_by_filename = {
            "setup.cfg" : DEFAULT_CONFIGPARSER_SETUP_CFG_STR,
            "setup.py"  : DEFAULT_CONFIGPARSER_SETUP_PY_STR,
            "README.rst": DEFAULT_CONFIGPARSER_README_RST_STR,
            "README.md" : DEFAULT_CONFIGPARSER_README_MD_STR,
        }
    elif ctx.config_format == 'toml':
        base_str = DEFAULT_TOML_BASE_STR

        default_pattern_strs_by_filename = {
            "pyproject.toml": DEFAULT_TOML_PYPROJECT_STR,
            "pycalver.toml" : DEFAULT_TOML_PYCALVER_STR,
            "setup.py"      : DEFAULT_TOML_SETUP_PY_STR,
            "README.rst"    : DEFAULT_TOML_README_RST_STR,
            "README.md"     : DEFAULT_TOML_README_MD_STR,
        }
    else:
        raise ValueError(f"Invalid fmt='{fmt}', must be either 'toml' or 'cfg'.")

    initial_version = dt.datetime.now().strftime("v%Y%m.0001-dev")

    cfg_str = base_str.format(initial_version=initial_version)

    for filename, default_str in default_pattern_strs_by_filename.items():
        if (ctx.path / filename).exists():
            cfg_str += default_str

    has_config_file = (
        (ctx.path / "setup.cfg").exists() or
        (ctx.path / "pyproject.toml").exists() or
        (ctx.path / "pycalver.toml").exists()
    )

    if not has_config_file:
        if ctx.config_format == 'cfg':
            cfg_str += DEFAULT_CONFIGPARSER_SETUP_CFG_STR
        if ctx.config_format == 'toml':
            cfg_str += DEFAULT_TOML_PYCALVER_STR

    cfg_str += "\n"

    return cfg_str


def write_content(cfg: Config) -> None:
    cfg_content = "\n" + "\n".join(cfg_lines)
    if os.path.exists("pyproject.toml"):
        with io.open("pyproject.toml", mode="at", encoding="utf-8") as fh:
            fh.write(cfg_content)
        print("Updated pyproject.toml")
    elif os.path.exists("setup.cfg"):
        with io.open("setup.cfg", mode="at", encoding="utf-8") as fh:
            fh.write(cfg_content)
        print("Updated setup.cfg")
    else:
        cfg_content = "\n".join(cfg_lines)
        with io.open("pycalver.toml", mode="at", encoding="utf-8") as fh:
            fh.write(cfg_content)
        print("Created pycalver.toml")
