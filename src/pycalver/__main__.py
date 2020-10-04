#!/usr/bin/env python
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
__main__ module for PyCalVer.

Enables use as module: $ python -m pycalver --version
"""
import io
import sys
import typing as typ
import logging
import datetime as dt
import subprocess as sp

import click
import colorama

from . import vcs
from . import v1cli
from . import v2cli
from . import config
from . import rewrite
from . import version
from . import patterns
from . import regexfmt
from . import v1rewrite
from . import v1version
from . import v2rewrite
from . import v2version
from . import v1patterns
from . import v2patterns

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


click.disable_unicode_literals_warning = True

logger = logging.getLogger("pycalver.__main__")


_VERBOSE = 0


def _configure_logging(verbose: int = 0) -> None:
    # pylint:disable=global-statement; global flag is global.
    global _VERBOSE
    _VERBOSE = verbose

    if verbose >= 2:
        log_format = "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)-17s - %(message)s"
        log_level  = logging.DEBUG
    elif verbose == 1:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO
    else:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO

    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")
    logger.debug("Logging configured.")


VALID_RELEASE_TAG_VALUES = ("alpha", "beta", "rc", "post", "final")


_current_date = dt.date.today().isoformat()


def _validate_date(date: typ.Optional[str], pin_date: bool) -> typ.Optional[dt.date]:
    if date and pin_date:
        logger.error(f"Can only use either --pin-date or --date='{date}', not both.")
        sys.exit(1)

    if date is None:
        return None

    try:
        dt_val = dt.datetime.strptime(date, "%Y-%m-%d")
        return dt_val.date()
    except ValueError:
        logger.error(
            f"Invalid parameter --date='{date}', must match format YYYY-0M-0D.", exc_info=True
        )
        sys.exit(1)


def _validate_release_tag(tag: typ.Optional[str]) -> None:
    if tag is None:
        return

    if tag in VALID_RELEASE_TAG_VALUES:
        return

    logger.error(f"Invalid argument --release={tag}")
    logger.error(f"Valid arguments are: {', '.join(VALID_RELEASE_TAG_VALUES)}")
    sys.exit(1)


@click.group()
@click.version_option(version="v202010.1040-beta")
@click.help_option()
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
def cli(verbose: int = 0) -> None:
    """Automatically update PyCalVer version strings in all project files."""
    _configure_logging(verbose=max(_VERBOSE, verbose))


@cli.command()
@click.argument("old_version")
@click.argument("pattern", default="{pycalver}")
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
@click.option(
    "--release",
    default=None,
    metavar="<NAME>",
    help=(
        f"Override release name of current_version. Valid options are: "
        f"{', '.join(VALID_RELEASE_TAG_VALUES)}."
    ),
)
@click.option("--major"   , is_flag=True, default=False, help="Increment major component.")
@click.option("-m"        , "--minor", is_flag=True, default=False, help="Increment minor component.")
@click.option("-p"        , "--patch", is_flag=True, default=False, help="Increment patch component.")
@click.option("-r"        , "--release-num", is_flag=True, default=False, help="Increment release number.")
@click.option("--pin-date", is_flag=True, default=False, help="Leave date components unchanged.")
@click.option(
    "--date",
    default=None,
    metavar="<ISODATE>",
    help=f"Set explicit date in format YYYY-0M-0D (e.g. {_current_date}).",
)
def test(
    old_version: str,
    pattern    : str = "{pycalver}",
    verbose    : int = 0,
    release    : str = None,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
    release_num: bool = False,
    pin_date   : bool = False,
    date       : typ.Optional[str] = None,
) -> None:
    """Increment a version number for demo purposes."""
    _configure_logging(verbose=max(_VERBOSE, verbose))
    raw_pattern = pattern  # use internal naming convention

    tag = release  # use internal naming convention
    _validate_release_tag(tag)
    _date = _validate_date(date, pin_date)

    new_version = incr_dispatch(
        old_version,
        raw_pattern=raw_pattern,
        tag=tag,
        major=major,
        minor=minor,
        patch=patch,
        release_num=release_num,
        pin_date=pin_date,
        date=_date,
    )
    if new_version is None:
        logger.error(f"Invalid version '{old_version}' and/or pattern '{raw_pattern}'.")
        sys.exit(1)

    pep440_version = version.to_pep440(new_version)

    click.echo(f"New Version: {new_version}")
    click.echo(f"PEP440     : {pep440_version}")


def _grep_text(pattern: patterns.Pattern, text: str, color: bool) -> typ.Iterable[str]:
    all_lines   = text.splitlines()
    for match in pattern.regexp.finditer(text):
        match_start, match_end = match.span()

        line_idx   = text[:match_start].count("\n")
        line_start = text.rfind("\n", 0, match_start) + 1
        line_end   = text.find("\n", match_end, -1)
        if color:
            matched_line = (
                text[line_start:match_start]
                + colorama.Style.BRIGHT
                + text[match_start:match_end]
                + colorama.Style.RESET_ALL
                + text[match_end:line_end]
            )
        else:
            matched_line = (
                text[line_start:match_start]
                + text[match_start:match_end]
                + text[match_end:line_end]
            )

        lines_offset = max(0, line_idx - 1) + 1
        lines        = all_lines[line_idx - 1 : line_idx + 2]

        if line_idx == 0:
            lines[0] = matched_line
        else:
            lines[1] = matched_line

        prefixed_lines = [
            f"{lines_offset + i:>4}: {line}"
            for i, line in enumerate(lines)
        ]
        yield "\n".join(prefixed_lines)


def _grep(
    raw_pattern: str,
    file_ios   : typ.Tuple[io.TextIOWrapper],
    color      : bool,
) -> None:
    pattern = v2patterns.compile_pattern(raw_pattern)

    match_count = 0
    for file_io in file_ios:
        text = file_io.read()

        match_strs = list(_grep_text(pattern, text, color))
        if len(match_strs) > 0:
            print(file_io.name)
            for match_str in match_strs:
                print(match_str)
            print()

        match_count += len(match_strs)

    if match_count == 0:
        logger.error(f"Pattern not found: '{raw_pattern}'")

    if match_count == 0 or _VERBOSE:
        pyexpr_regex = regexfmt.pyexpr_regex(pattern.regexp.pattern)

        print("# " + regexfmt.regex101_url(pattern.regexp.pattern))
        print(pyexpr_regex)
        print()

    if match_count == 0:
        sys.exit(1)


@cli.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Control log level. -vv for debug level.",
)
@click.option(
    "--version-pattern",
    default=None,
    metavar="<PATTERN>",
    help="Pattern to use for placeholders: {version}/{pep440_version}",
)
@click.argument("pattern")
@click.argument('files', nargs=-1, type=click.File('r'))
def grep(
    pattern        : str,
    files          : typ.Tuple[io.TextIOWrapper],
    version_pattern: typ.Optional[str] = None,
    verbose        : int = 0,
) -> None:
    """Search file(s) for a version pattern."""
    verbose = max(_VERBOSE, verbose)
    _configure_logging(verbose)

    raw_pattern = pattern  # use internal naming convention

    is_version_pattern_required = "{version}" in raw_pattern or "{pep440_version}" in raw_pattern

    if is_version_pattern_required and version_pattern is None:
        logger.error(
            "Argument --version-pattern=<PATTERN> is required"
            " for placeholders: {version}/{pep440_version}."
        )
        sys.exit(1)
    elif is_version_pattern_required:
        normalize_pattern = v2patterns.normalize_pattern(version_pattern, raw_pattern)
    else:
        normalize_pattern = raw_pattern

    isatty = getattr(sys.stdout, 'isatty', lambda: False)

    if isatty():
        colorama.init()
        try:
            _grep(normalize_pattern, files, color=True)
        finally:
            colorama.deinit()
    else:
        _grep(normalize_pattern, files, color=False)


@cli.command()
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
@click.option(
    "-f/-n", "--fetch/--no-fetch", is_flag=True, default=True, help="Sync tags from remote origin."
)
def show(verbose: int = 0, fetch: bool = True) -> None:
    """Show current version of your project."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    _, cfg = config.init(project_path=".")

    if cfg is None:
        logger.error("Could not parse configuration. Perhaps try 'pycalver init'.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)
    click.echo(f"Current Version: {cfg.current_version}")
    click.echo(f"PEP440         : {cfg.pep440_version}")


def _colored_diff_lines(diff: str) -> typ.Iterable[str]:
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            yield line
        elif line.startswith("+"):
            yield "\u001b[32m" + line + "\u001b[0m"
        elif line.startswith("-"):
            yield "\u001b[31m" + line + "\u001b[0m"
        elif line.startswith("@"):
            yield "\u001b[36m" + line + "\u001b[0m"
        else:
            yield line


def _print_diff_str(diff: str) -> None:
    colored_diff = "\n".join(_colored_diff_lines(diff))
    if sys.stdout.isatty():
        click.echo(colored_diff)
    else:
        click.echo(diff)


def _print_diff(cfg: config.Config, new_version: str) -> None:
    try:
        if cfg.is_new_pattern:
            diff = v2cli.get_diff(cfg, new_version)
        else:
            diff = v1cli.get_diff(cfg, new_version)

        _print_diff_str(diff)
    except rewrite.NoPatternMatch as ex:
        logger.error(str(ex))
        sys.exit(1)


def incr_dispatch(
    old_version: str,
    raw_pattern: str,
    *,
    tag        : str = None,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
    release_num: bool = False,
    pin_date   : bool = False,
    date       : typ.Optional[dt.date] = None,
) -> typ.Optional[str]:
    v1_parts    = list(v1patterns.PART_PATTERNS) + list(v1patterns.FULL_PART_FORMATS)
    has_v1_part = any("{" + part + "}" in raw_pattern for part in v1_parts)

    if _VERBOSE:
        if has_v1_part:
            pattern = v1patterns.compile_pattern(raw_pattern)
        else:
            pattern = v2patterns.compile_pattern(raw_pattern)

        logger.info("Using pattern " + raw_pattern)
        logger.info("regex = " + regexfmt.pyexpr_regex(pattern.regexp.pattern))

    if has_v1_part:
        return v1version.incr(
            old_version,
            raw_pattern=raw_pattern,
            tag=tag,
            major=major,
            minor=minor,
            patch=patch,
            release_num=release_num,
            pin_date=pin_date,
            date=date,
        )
    else:
        return v2version.incr(
            old_version,
            raw_pattern=raw_pattern,
            tag=tag,
            major=major,
            minor=minor,
            patch=patch,
            release_num=release_num,
            pin_date=pin_date,
            date=date,
        )


def _bump(
    cfg           : config.Config,
    new_version   : str,
    commit_message: str,
    allow_dirty   : bool = False,
) -> None:
    vcs_api: typ.Optional[vcs.VCSAPI] = None

    if cfg.commit:
        try:
            vcs_api = vcs.get_vcs_api()
        except OSError:
            logger.warning("Version Control System not found, skipping commit.")

    filepaths = set(cfg.file_patterns.keys())

    if vcs_api:
        vcs.assert_not_dirty(vcs_api, filepaths, allow_dirty)

    try:
        if cfg.is_new_pattern:
            new_v2_vinfo = v2version.parse_version_info(new_version, cfg.version_pattern)
            v2rewrite.rewrite_files(cfg.file_patterns, new_v2_vinfo)
        else:
            new_v1_vinfo = v1version.parse_version_info(new_version, cfg.version_pattern)
            v1rewrite.rewrite_files(cfg.file_patterns, new_v1_vinfo)
    except rewrite.NoPatternMatch as ex:
        logger.error(str(ex))
        sys.exit(1)

    if vcs_api:
        vcs.commit(cfg, vcs_api, filepaths, new_version, commit_message)


def _try_bump(
    cfg           : config.Config,
    new_version   : str,
    commit_message: str,
    allow_dirty   : bool = False,
) -> None:
    try:
        _bump(cfg, new_version, commit_message, allow_dirty)
    except sp.CalledProcessError as ex:
        logger.error(f"Error running subcommand: {ex.cmd}")
        if ex.stdout:
            sys.stdout.write(ex.stdout.decode('utf-8'))
        if ex.stderr:
            sys.stderr.write(ex.stderr.decode('utf-8'))
        sys.exit(1)


@cli.command()
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
@click.option(
    '-d', "--dry", default=False, is_flag=True, help="Display diff of changes, don't rewrite files."
)
def init(verbose: int = 0, dry: bool = False) -> None:
    """Initialize [pycalver] configuration."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    ctx, cfg = config.init(project_path=".", cfg_missing_ok=True)

    if cfg:
        logger.error(f"Configuration already initialized in {ctx.config_rel_path}")
        sys.exit(1)

    if dry:
        click.echo(f"Exiting because of '-d/--dry'. Would have written to {ctx.config_rel_path}:")
        cfg_text: str = config.default_config(ctx)
        click.echo("\n    " + "\n    ".join(cfg_text.splitlines()))
        sys.exit(0)

    config.write_content(ctx)


def _update_cfg_from_vcs(cfg: config.Config, fetch: bool) -> config.Config:
    all_tags = vcs.get_tags(fetch=fetch)

    if cfg.is_new_pattern:
        return v2cli.update_cfg_from_vcs(cfg, all_tags)
    else:
        return v1cli.update_cfg_from_vcs(cfg, all_tags)


@cli.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Control log level. -vv for debug level.",
)
@click.option(
    "-f/-n",
    "--fetch/--no-fetch",
    is_flag=True,
    default=True,
    help="Sync tags from remote origin.",
)
@click.option(
    "-d",
    "--dry",
    default=False,
    is_flag=True,
    help="Display diff of changes, don't rewrite files.",
)
@click.option(
    "--release",
    default=None,
    metavar="<NAME>",
    help=(
        f"Override release name of current_version. Valid options are: "
        f"{', '.join(VALID_RELEASE_TAG_VALUES)}."
    ),
)
@click.option(
    "--allow-dirty",
    default=False,
    is_flag=True,
    help=(
        "Commit even when working directory is has uncomitted changes. "
        "(WARNING: The commit will still be aborted if there are uncomitted "
        "to files with version strings."
    ),
)
@click.option("--major", is_flag=True, default=False, help="Increment major component.")
@click.option("-m", "--minor", is_flag=True, default=False, help="Increment minor component.")
@click.option("-p", "--patch", is_flag=True, default=False, help="Increment patch component.")
@click.option("-r", "--release-num", is_flag=True, default=False, help="Increment release number.")
@click.option("--pin-date", is_flag=True, default=False, help="Leave date components unchanged.")
@click.option(
    "--date",
    default=None,
    metavar="<ISODATE>",
    help=f"Set explicit date in format YYYY-0M-0D (e.g. {_current_date}).",
)
def bump(
    release    : typ.Optional[str] = None,
    verbose    : int = 0,
    dry        : bool = False,
    allow_dirty: bool = False,
    fetch      : bool = True,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
    release_num: bool = False,
    pin_date   : bool = False,
    date       : typ.Optional[str] = None,
) -> None:
    """Increment the current version string and update project files."""
    verbose = max(_VERBOSE, verbose)
    _configure_logging(verbose)

    tag = release  # use internal naming convention
    _validate_release_tag(tag)
    _date = _validate_date(date, pin_date)

    _, cfg = config.init(project_path=".")

    if cfg is None:
        logger.error("Could not parse configuration. Perhaps try 'pycalver init'.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)

    old_version = cfg.current_version
    new_version = incr_dispatch(
        old_version,
        raw_pattern=cfg.version_pattern,
        tag=tag,
        major=major,
        minor=minor,
        patch=patch,
        release_num=release_num,
        pin_date=pin_date,
        date=_date,
    )

    if new_version is None:
        is_semver = "{semver}" in cfg.version_pattern or (
            "MAJOR" in cfg.version_pattern
            and "MAJOR" in cfg.version_pattern
            and "PATCH" in cfg.version_pattern
        )
        has_semver_inc = major or minor or patch
        if is_semver and not has_semver_inc:
            logger.warning("bump --major/--minor/--patch required when using semver.")
        else:
            logger.error(f"Invalid version '{old_version}' and/or pattern '{cfg.version_pattern}'.")
        sys.exit(1)

    logger.info(f"Old Version: {old_version}")
    logger.info(f"New Version: {new_version}")

    if dry or verbose >= 2:
        _print_diff(cfg, new_version)

    if dry:
        return

    commit_message_kwargs = {
        'new_version'       : new_version,
        'old_version'       : old_version,
        'new_version_pep440': version.to_pep440(new_version),
        'old_version_pep440': version.to_pep440(old_version),
    }
    commit_message = cfg.commit_message.format(**commit_message_kwargs)

    _try_bump(cfg, new_version, commit_message, allow_dirty)


if __name__ == '__main__':
    cli()
