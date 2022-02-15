# This file is part of the bumpver project
# https://gitlab.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Parse bumpver.toml, setup.cfg or pyproject.toml files."""

import re
import typing as typ
import logging
import datetime as dt
import configparser

import toml
import pathlib2 as pl

from . import version
from . import v1version
from . import v2version
from . import v1patterns
from . import v2patterns
from .patterns import Pattern

logger = logging.getLogger("bumpver.config")

RawPatterns         = typ.List[str]
RawPatternsByFile   = typ.Dict[str, RawPatterns]
FileRawPatternsItem = typ.Tuple[str, RawPatterns]

PatternsByFile   = typ.Dict[str, typ.List[Pattern]]
FilePatternsItem = typ.Tuple[str, typ.List[Pattern]]


SUPPORTED_CONFIGS = ["setup.cfg", "pyproject.toml", "pycalver.toml", "bumpver.toml"]

DEFAULT_COMMIT_MESSAGE = "bump version to {new_version}"


class ProjectContext(typ.NamedTuple):
    """Container class for project info."""

    path           : pl.Path
    config_filepath: pl.Path
    config_rel_path: str
    config_format  : str
    vcs_type       : typ.Optional[str]


def _pick_config_filepath(path: pl.Path) -> pl.Path:
    config_candidates: typ.List[pl.Path] = [
        path / "pycalver.toml",
        path / "bumpver.toml",
        path / "pyproject.toml",
        path / "setup.cfg",
    ]

    # Prefer to use a config which contains a bumpver and current_version
    # This means a project can have multiple different configs.
    for config_filepath in config_candidates:
        if config_filepath.exists():
            with config_filepath.open(mode="rb") as fobj:
                data = fobj.read()

            has_bumpver_section = (
                b"bumpver]" in data or b"pycalver]" in data
            ) and b"current_version" in data
            if has_bumpver_section:
                return config_filepath

    # Next pick whatever config happens to exist, even if it
    # doesn't have a [bumpver] section (yet).
    for config_filepath in config_candidates:
        if config_filepath.exists():
            return config_filepath

    # fallback to creating a new bumpver.toml
    return path / "bumpver.toml"


def _parse_config_and_format(path: pl.Path) -> typ.Tuple[pl.Path, str, str]:
    config_filepath = _pick_config_filepath(path)

    if config_filepath.is_absolute():
        config_rel_path = str(config_filepath.relative_to(path.absolute()))
    else:
        config_rel_path = str(config_filepath)
        config_filepath = pl.Path.cwd() / config_filepath

    config_format = config_filepath.suffix[1:]
    return (config_filepath, config_rel_path, config_format)


def init_project_ctx(project_path: typ.Union[str, pl.Path, None] = ".") -> ProjectContext:
    """Initialize ProjectContext from a path."""
    if isinstance(project_path, pl.Path):
        path = project_path
    elif project_path is None:
        path = pl.Path(".")
    else:
        # assume it's a str/unicode
        path = pl.Path(project_path)

    config_filepath, config_rel_path, config_format = _parse_config_and_format(path)

    vcs_type: typ.Optional[str]

    if (path / ".git").exists():
        vcs_type = 'git'
    elif (path / ".hg").exists():
        vcs_type = 'hg'
    else:
        vcs_type = None

    return ProjectContext(path, config_filepath, config_rel_path, config_format, vcs_type)


RawConfig      = typ.Dict[str, typ.Any]
MaybeRawConfig = typ.Optional[RawConfig]


class Config(typ.NamedTuple):
    """Container for parameters parsed from a config file."""

    current_version: str
    version_pattern: str
    pep440_version : str
    commit_message : str

    commit        : bool
    tag           : bool
    push          : bool
    is_new_pattern: bool

    file_patterns: PatternsByFile


MaybeConfig = typ.Optional[Config]


def _debug_str(cfg: Config) -> str:
    cfg_str_parts = [
        "Config Parsed: Config(",
        f"\n    current_version='{cfg.current_version}',",
        f"\n    version_pattern='{cfg.version_pattern}',",
        f"\n    pep440_version='{cfg.pep440_version}',",
        f"\n    commit_message='{cfg.commit_message}',",
        f"\n    commit={cfg.commit},",
        f"\n    tag={cfg.tag},",
        f"\n    push={cfg.push},",
        f"\n    is_new_pattern={cfg.is_new_pattern},",
        "\n    file_patterns={",
    ]

    for filepath, patterns in sorted(cfg.file_patterns.items()):
        for pattern in patterns:
            cfg_str_parts.append(f"\n        '{filepath}': '{pattern.raw_pattern}',")

    cfg_str_parts += ["\n    }\n)"]
    return "".join(cfg_str_parts)


def _parse_cfg_file_patterns(
    cfg_parser: configparser.RawConfigParser,
) -> typ.Iterable[FileRawPatternsItem]:
    file_pattern_items: typ.List[typ.Tuple[str, str]]

    if cfg_parser.has_section("pycalver:file_patterns"):
        file_pattern_items = cfg_parser.items("pycalver:file_patterns")
    elif cfg_parser.has_section("bumpver:file_patterns"):
        file_pattern_items = cfg_parser.items("bumpver:file_patterns")
    else:
        return

    for filepath, patterns_str in file_pattern_items:
        maybe_patterns = (line.strip() for line in patterns_str.splitlines())
        patterns       = [p for p in maybe_patterns if p]
        yield filepath, patterns


class _ConfigParser(configparser.RawConfigParser):
    # pylint:disable=too-many-ancestors ; from our perspective, it's just one
    """Custom parser, simply to override optionxform behaviour."""

    def optionxform(self, optionstr: str) -> str:
        """Non-xforming (ie. uppercase preserving) override.

        This is important because our option names are actually
        filenames, so case sensitivity is relevant. The default
        behaviour is to do optionstr.lower()
        """
        return optionstr


OptionVal = typ.Union[str, bool, None]

BOOL_OPTIONS: typ.Mapping[str, OptionVal] = {'commit': False, 'tag': None, 'push': None}


def _parse_cfg(cfg_buffer: typ.IO[str]) -> RawConfig:
    cfg_parser = _ConfigParser()

    if hasattr(cfg_parser, 'read_file'):
        cfg_parser.read_file(cfg_buffer)
    else:
        cfg_parser.readfp(cfg_buffer)  # pylint: disable=deprecated-method ; python2 compat

    raw_cfg: RawConfig
    if cfg_parser.has_section("pycalver"):
        raw_cfg = dict(cfg_parser.items("pycalver"))
    elif cfg_parser.has_section("bumpver"):
        raw_cfg = dict(cfg_parser.items("bumpver"))
    else:
        logger.warning("Perhaps try 'bumpver init'.")
        raise ValueError("Missing [bumpver] section.")

    for option, default_val in BOOL_OPTIONS.items():
        val: OptionVal = raw_cfg.get(option, default_val)
        if isinstance(val, (bytes, str)):
            val = val.lower() in ("yes", "true", "1", "on")
        raw_cfg[option] = val

    raw_cfg['file_patterns'] = dict(_parse_cfg_file_patterns(cfg_parser))

    _set_raw_config_defaults(raw_cfg)

    return raw_cfg


def _parse_toml(cfg_buffer: typ.IO[str]) -> RawConfig:
    raw_full_cfg: typ.Any = toml.load(cfg_buffer)
    raw_cfg     : RawConfig

    if 'tool' in raw_full_cfg and 'bumpver' in raw_full_cfg['tool']:
        raw_cfg = raw_full_cfg['tool']['bumpver']
    elif 'bumpver' in raw_full_cfg:
        raw_cfg = raw_full_cfg['bumpver']
    elif 'pycalver' in raw_full_cfg:
        raw_cfg = raw_full_cfg['pycalver']
    else:
        raw_cfg = {}

    for option, default_val in BOOL_OPTIONS.items():
        raw_cfg[option] = raw_cfg.get(option, default_val)

    _set_raw_config_defaults(raw_cfg)

    return raw_cfg


def _iter_glob_expanded_file_patterns(
    raw_patterns_by_file: RawPatternsByFile,
) -> typ.Iterator[FileRawPatternsItem]:
    for filepath_glob, raw_patterns in raw_patterns_by_file.items():
        filepaths = list(pl.Path().glob(filepath_glob))

        if filepaths:
            for filepath in filepaths:
                yield str(filepath), raw_patterns
        else:
            logger.warning(f"Invalid config, no such file: {filepath_glob}")
            # fallback to treating it as a simple path
            yield filepath_glob, raw_patterns


def _compile_v1_file_patterns(raw_cfg: RawConfig) -> typ.Iterator[FilePatternsItem]:
    """Create inernal/compiled representation of the file_patterns config field.

    The result the same, regardless of the config format.
    """
    # current_version: str = raw_cfg['current_version']
    # current_pep440_version = version.pep440_version(current_version)

    version_pattern     : str               = raw_cfg['version_pattern']
    raw_patterns_by_file: RawPatternsByFile = raw_cfg['file_patterns']

    for filepath, raw_patterns in _iter_glob_expanded_file_patterns(raw_patterns_by_file):
        compiled_patterns = v1patterns.compile_patterns(version_pattern, raw_patterns)
        yield filepath, compiled_patterns


def _compile_v2_file_patterns(raw_cfg: RawConfig) -> typ.Iterable[FilePatternsItem]:
    """Create inernal/compiled representation of the file_patterns config field.

    The result the same, regardless of the config format.
    """
    version_pattern     : str               = raw_cfg['version_pattern']
    raw_patterns_by_file: RawPatternsByFile = raw_cfg['file_patterns']

    for filepath, raw_patterns in _iter_glob_expanded_file_patterns(raw_patterns_by_file):
        for raw_pattern in raw_patterns:
            if raw_pattern.startswith("["):
                errmsg = (
                    f"Invalid pattern {raw_pattern} for {filepath}. "
                    + "Character not valid in this position '[' "
                )
                raise ValueError(errmsg)

            # provoke error for specifc pattern
            try:
                v2patterns.compile_pattern(version_pattern, raw_pattern)
            except re.error:
                logger.warning(f"Invalid patterns for {filepath} ({raw_pattern})")
                raise

        compiled_patterns = v2patterns.compile_patterns(version_pattern, raw_patterns)
        yield filepath, compiled_patterns


def _compile_file_patterns(raw_cfg: RawConfig, is_new_pattern: bool) -> PatternsByFile:
    if is_new_pattern:
        _file_pattern_items = _compile_v2_file_patterns(raw_cfg)
    else:
        _file_pattern_items = _compile_v1_file_patterns(raw_cfg)

    # NOTE (mb 2020-10-03): There can be multiple items for the same
    #   path, so this is not an option:
    #
    # return dict(_file_pattern_items)

    file_patterns: PatternsByFile = {}
    for path, patterns in _file_pattern_items:
        if path in file_patterns:
            file_patterns[path].extend(patterns)
        else:
            file_patterns[path] = patterns
    return file_patterns


def _validate_version_with_pattern(
    current_version: str,
    version_pattern: str,
    is_new_pattern : bool,
) -> None:
    """Provoke ValueError if version_pattern and current_version are not compatible."""
    try:
        if is_new_pattern:
            v2version.parse_version_info(current_version, version_pattern)
        else:
            v1version.parse_version_info(current_version, version_pattern)
    except version.PatternError:
        errmsg = (
            "Invalid configuration. "
            f"current_version='{current_version}' is invalid for "
            f"version_pattern='{version_pattern}'"
        )
        raise ValueError(errmsg)

    if is_new_pattern:
        invalid_chars = re.search(r"([\s]+)", version_pattern)
        if invalid_chars:
            errmsg = (
                f"Invalid character(s) '{invalid_chars.group(1)}'"
                f' in version_pattern = "{version_pattern}"'
            )
            raise ValueError(errmsg)
        if not v2version.is_valid_week_pattern(version_pattern):
            errmsg = f"Invalid week number pattern: {version_pattern}"
            raise ValueError(errmsg)


def _parse_config(raw_cfg: RawConfig) -> Config:
    """Parse configuration which was loaded from an .ini/.cfg or .toml file."""

    commit_message: str = raw_cfg.get('commit_message', DEFAULT_COMMIT_MESSAGE)
    commit_message = raw_cfg['commit_message'] = commit_message.strip("'\" ")

    current_version: str = raw_cfg['current_version']
    current_version = raw_cfg['current_version'] = current_version.strip("'\" ")

    version_pattern: str = raw_cfg['version_pattern']
    version_pattern = raw_cfg['version_pattern'] = version_pattern.strip("'\" ")

    is_new_pattern = "{" not in version_pattern and "}" not in version_pattern

    _validate_version_with_pattern(current_version, version_pattern, is_new_pattern)

    pep440_version = version.to_pep440(current_version)

    file_patterns = _compile_file_patterns(raw_cfg, is_new_pattern)

    commit = raw_cfg['commit']
    tag    = raw_cfg['tag']
    push   = raw_cfg['push']

    if tag is None:
        tag = raw_cfg['tag'] = False
    if push is None:
        push = raw_cfg['push'] = False

    if tag and not commit:
        raise ValueError("commit=True required if tag=True")

    if push and not commit:
        raise ValueError("commit=True required if push=True")

    cfg = Config(
        current_version=current_version,
        version_pattern=version_pattern,
        pep440_version=pep440_version,
        commit_message=commit_message,
        commit=commit,
        tag=tag,
        push=push,
        is_new_pattern=is_new_pattern,
        file_patterns=file_patterns,
    )
    logger.debug(_debug_str(cfg))
    return cfg


def _parse_current_version_default_pattern(raw_cfg: RawConfig, raw_cfg_text: str) -> str:
    is_config_section = False
    for line in raw_cfg_text.splitlines():
        if is_config_section and line.startswith("current_version"):
            current_version: str = raw_cfg['current_version']
            version_pattern: str = raw_cfg['version_pattern']
            return line.replace(current_version, version_pattern)

        if line.strip() == "[pycalver]":
            is_config_section = True
        elif line.strip() == "[bumpver]":
            is_config_section = True
        elif line.strip() == "[tool.bumpver]":
            is_config_section = True
        elif line and line[0] == "[" and line[-1] == "]":
            is_config_section = False

    raise ValueError("Could not parse 'current_version'")


def _set_raw_config_defaults(raw_cfg: RawConfig) -> None:
    if 'version_pattern' not in raw_cfg:
        raise TypeError("Missing version_pattern")
    elif not isinstance(raw_cfg['version_pattern'], str):
        err = f"Invalid type for version_pattern = {raw_cfg['version_pattern']}"
        raise TypeError(err)

    if 'current_version' not in raw_cfg:
        raise ValueError("Missing 'current_version' configuration")
    elif not isinstance(raw_cfg['current_version'], str):
        err = f"Invalid type for current_version = {raw_cfg['current_version']}"
        raise TypeError(err)

    if 'file_patterns' not in raw_cfg:
        raw_cfg['file_patterns'] = {}


def _parse_raw_config(ctx: ProjectContext) -> RawConfig:
    with ctx.config_filepath.open(mode="rt", encoding="utf-8") as fobj:
        if ctx.config_format == 'toml':
            raw_cfg = _parse_toml(fobj)
        elif ctx.config_format == 'cfg':
            raw_cfg = _parse_cfg(fobj)
        else:
            err_msg = (
                f"Invalid config_format='{ctx.config_format}'."
                "Supported formats are 'setup.cfg' and 'pyproject.toml'"
            )
            raise RuntimeError(err_msg)

    if ctx.config_rel_path not in raw_cfg['file_patterns']:
        with ctx.config_filepath.open(mode="rt", encoding="utf-8") as fobj:
            raw_cfg_text = fobj.read()

        # NOTE (mb 2020-09-19): By default we always add
        #   a pattern for the config section itself.
        raw_version_pattern = _parse_current_version_default_pattern(raw_cfg, raw_cfg_text)
        raw_cfg['file_patterns'][ctx.config_rel_path] = [raw_version_pattern]

    return raw_cfg


def parse(ctx: ProjectContext, cfg_missing_ok: bool = False) -> MaybeConfig:
    """Parse config file if available."""
    if ctx.config_filepath.exists():
        try:
            raw_cfg = _parse_raw_config(ctx)
            return _parse_config(raw_cfg)
        except (TypeError, ValueError) as ex:
            logger.warning(f"Couldn't parse {ctx.config_rel_path}: {str(ex)}")
            return None
    elif cfg_missing_ok:
        return None
    else:
        logger.warning(f"File not found: {ctx.config_rel_path}")
        return None


def init(
    project_path  : typ.Union[str, pl.Path, None] = ".",
    cfg_missing_ok: bool = False,
) -> typ.Tuple[ProjectContext, MaybeConfig]:
    ctx = init_project_ctx(project_path)
    cfg = parse(ctx, cfg_missing_ok)
    return (ctx, cfg)


DEFAULT_CONFIGPARSER_BASE_TMPL = """
[bumpver]
current_version = "{initial_version}"
version_pattern = "YYYY.BUILD[-TAG]"
commit_message = "bump version {{old_version}} -> {{new_version}}"
commit = True
tag = True
push = True

[bumpver:file_patterns]
""".lstrip()


DEFAULT_CONFIGPARSER_SETUP_CFG_STR = """
setup.cfg =
    current_version = "{version}"
""".lstrip()


DEFAULT_CONFIGPARSER_SETUP_PY_STR = """
setup.py =
    "{version}"
    "{pep440_version}"
""".lstrip()


DEFAULT_CONFIGPARSER_README_RST_STR = """
README.rst =
    {version}
    {pep440_version}
""".lstrip()


DEFAULT_CONFIGPARSER_README_MD_STR = """
README.md =
    {version}
    {pep440_version}
""".lstrip()


DEFAULT_PYPROJECT_TOML_BASE_TMPL = """
[tool.bumpver]
current_version = "{initial_version}"
version_pattern = "YYYY.BUILD[-TAG]"
commit_message = "bump version {{old_version}} -> {{new_version}}"
commit = true
tag = true
push = true

[tool.bumpver.file_patterns]
""".lstrip()


DEFAULT_BUMPVER_TOML_BASE_TMPL = """
[bumpver]
current_version = "{initial_version}"
version_pattern = "YYYY.BUILD[-TAG]"
commit_message = "bump version {{old_version}} -> {{new_version}}"
commit = true
tag = true
push = true

[bumpver.file_patterns]
""".lstrip()


DEFAULT_TOML_PYCALVER_STR = """
"pycalver.toml" = [
    'current_version = "{version}"',
]
""".lstrip()


DEFAULT_TOML_BUMPVER_STR = """
"bumpver.toml" = [
    'current_version = "{version}"',
]
""".lstrip()


DEFAULT_TOML_PYPROJECT_STR = """
"pyproject.toml" = [
    'current_version = "{version}"',
]
""".lstrip()


DEFAULT_TOML_SETUP_PY_STR = """
"setup.py" = [
    "{version}",
    "{pep440_version}",
]
""".lstrip()


DEFAULT_TOML_README_RST_STR = """
"README.rst" = [
    "{version}",
    "{pep440_version}",
]
""".lstrip()


DEFAULT_TOML_README_MD_STR = """
"README.md" = [
    "{version}",
    "{pep440_version}",
]
""".lstrip()


def _initial_version() -> str:
    return dt.datetime.utcnow().strftime("%Y.1001-alpha")


def _initial_version_pep440() -> str:
    return dt.datetime.utcnow().strftime("%Y.1001a0")


def default_config(ctx: ProjectContext) -> str:
    """Generate initial default config."""
    fmt = ctx.config_format
    if fmt == 'cfg':
        base_tmpl = DEFAULT_CONFIGPARSER_BASE_TMPL

        default_pattern_strs_by_filename = {
            "setup.cfg" : DEFAULT_CONFIGPARSER_SETUP_CFG_STR,
            "setup.py"  : DEFAULT_CONFIGPARSER_SETUP_PY_STR,
            "README.rst": DEFAULT_CONFIGPARSER_README_RST_STR,
            "README.md" : DEFAULT_CONFIGPARSER_README_MD_STR,
        }
    elif fmt == 'toml':
        if ctx.config_filepath.name == "pyproject.toml":
            base_tmpl = DEFAULT_PYPROJECT_TOML_BASE_TMPL
        else:
            base_tmpl = DEFAULT_BUMPVER_TOML_BASE_TMPL

        default_pattern_strs_by_filename = {
            "pyproject.toml": DEFAULT_TOML_PYPROJECT_STR,
            "pycalver.toml" : DEFAULT_TOML_PYCALVER_STR,
            "bumpver.toml"  : DEFAULT_TOML_BUMPVER_STR,
            "setup.py"      : DEFAULT_TOML_SETUP_PY_STR,
            "README.rst"    : DEFAULT_TOML_README_RST_STR,
            "README.md"     : DEFAULT_TOML_README_MD_STR,
        }
    else:
        raise ValueError(f"Invalid config_format='{fmt}', must be either 'toml' or 'cfg'.")

    cfg_str = base_tmpl.format(initial_version=_initial_version())

    for filename, default_str in default_pattern_strs_by_filename.items():
        if (ctx.path / filename).exists():
            cfg_str += default_str

    has_config_file = any((ctx.path / fn).exists() for fn in SUPPORTED_CONFIGS)

    if not has_config_file:
        if ctx.config_format == 'cfg':
            cfg_str += DEFAULT_CONFIGPARSER_SETUP_CFG_STR
        if ctx.config_format == 'toml':
            cfg_str += DEFAULT_TOML_BUMPVER_STR

    cfg_str += "\n"

    return cfg_str


def write_content(ctx: ProjectContext) -> None:
    """Update project config file with initial default config."""
    fobj: typ.IO[str]

    cfg_content = default_config(ctx)
    if ctx.config_filepath.exists():
        cfg_content = "\n" + cfg_content

    with ctx.config_filepath.open(mode="at", encoding="utf-8") as fobj:
        fobj.write(cfg_content)
    print(f"Updated {ctx.config_rel_path}")
