#!/usr/bin/env python
# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""cli module for BumpVer."""
import io
import sys
import typing as typ
import logging
import datetime as dt
import subprocess as sp

import click
import colorama

from . import vcs
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

logger = logging.getLogger("bumpver.cli")


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

    logger.error(f"Invalid argument --tag={tag}")
    logger.error(f"Valid arguments are: {', '.join(VALID_RELEASE_TAG_VALUES)}")
    sys.exit(1)


def _validate_flags(
    raw_pattern: str,
    major      : bool,
    minor      : bool,
    patch      : bool,
) -> None:
    if "{" in raw_pattern and "}" in raw_pattern:
        # only validate for new style patterns
        return

    valid = True
    if major and "MAJOR" not in raw_pattern:
        logger.error(f"Flag --major is not applicable to pattern '{raw_pattern}'")
        valid = False
    if minor and "MINOR" not in raw_pattern:
        logger.error(f"Flag --minor is not applicable to pattern '{raw_pattern}'")
        valid = False
    if patch and "PATCH" not in raw_pattern:
        logger.error(f"Flag --patch is not applicable to pattern '{raw_pattern}'")
        valid = False

    if not valid:
        sys.exit(1)


def _log_no_change(subcmd: str, version_pattern: str) -> None:
    is_semver = "{semver}" in version_pattern or (
        "MAJOR" in version_pattern and "MAJOR" in version_pattern and "PATCH" in version_pattern
    )
    if is_semver:
        logger.warning(f"bumpver {subcmd} [--major/--minor/--patch] required for use with SemVer.")
    else:
        available_flags = [
            "--" + part.lower() for part in ['MAJOR', 'MINOR', 'PATCH'] if part in version_pattern
        ]
        if available_flags:
            available_flags_str = "/".join(available_flags)
            logger.info(f"Perhaps try: bumpver {subcmd} {available_flags_str} ")


def _get_normalized_pattern(raw_pattern: str, version_pattern: typ.Optional[str]) -> str:
    is_version_pattern_required = "{version}" in raw_pattern or "{pep440_version}" in raw_pattern

    if is_version_pattern_required and version_pattern is None:
        logger.error(
            "Argument --version-pattern=<PATTERN> is required"
            " for placeholders: {version}/{pep440_version}."
        )
        sys.exit(1)
    elif version_pattern is None:
        _version_pattern = "INVALID"  # pacify mypy, it's not referenced in raw_pattern
    else:
        _version_pattern = version_pattern

    if is_version_pattern_required:
        return v2patterns.normalize_pattern(_version_pattern, raw_pattern)
    else:
        return raw_pattern


verbose_option = click.option(
    "-v",
    "--verbose",
    count=True,
    help="Control log level. -vv for debug level.",
)


dry_option = click.option(
    "-d",
    "--dry",
    default=False,
    is_flag=True,
    help="Display diff of changes, don't rewrite files.",
)


fetch_option = click.option(
    "-f/-n",
    "--fetch/--no-fetch",
    is_flag=True,
    default=True,
    help="Sync tags from remote origin.",
)


env_option = click.option(
    "-e",
    "--env",
    is_flag=True,
    default=False,
    help="Print version state for use with shell scripts: eval $(bumpver show --env)",
)


def version_options(function: typ.Callable) -> typ.Callable:
    decorators = [
        click.option("--major", is_flag=True, default=False, help="Increment major component."),
        click.option(
            "-m", "--minor", is_flag=True, default=False, help="Increment minor component."
        ),
        click.option(
            "-p", "--patch", is_flag=True, default=False, help="Increment patch component."
        ),
        click.option(
            "-t",
            "--tag",
            default=None,
            metavar="<NAME>",
            help=(
                "Override release tag of current_version. Valid options are: "
                f"{', '.join(VALID_RELEASE_TAG_VALUES)}."
            ),
        ),
        click.option(
            "--tag-num",
            is_flag=True,
            default=False,
            help="Increment release tag number (rc1, rc2, rc3..).",
        ),
        click.option(
            "--pin-date", is_flag=True, default=False, help="Leave date components unchanged."
        ),
        click.option(
            "--date",
            default=None,
            metavar="<ISODATE>",
            help=f"Set explicit date in format YYYY-0M-0D (e.g. {_current_date}).",
        ),
        click.option(
            "--set-version",
            default=None,
            metavar="<VERSION>",
            help="Set version explicitly.",
        ),
    ]
    decorated = function
    for decorator in decorators:
        decorated = decorator(decorated)
    return decorated


@click.group()
@click.version_option(version="2021.1112")
@click.help_option()
@verbose_option
def cli(verbose: int = 0) -> None:
    """Automatically update version strings in plaintext files."""
    if verbose:
        _configure_logging(verbose=max(_VERBOSE, verbose))


@cli.command()
@click.argument("old_version")
@click.argument("pattern")
@verbose_option
@version_options
def test(
    old_version: str,
    pattern    : str,
    verbose    : int = 0,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
    tag        : str = None,
    tag_num    : bool = False,
    pin_date   : bool = False,
    date       : typ.Optional[str] = None,
    set_version: typ.Optional[str] = None,
) -> None:
    """Increment a version number for demo purposes."""
    _configure_logging(verbose=max(_VERBOSE, verbose))
    _validate_release_tag(tag)

    raw_pattern = pattern  # use internal naming convention

    _validate_flags(raw_pattern, major, minor, patch)
    _date = _validate_date(date, pin_date)

    if set_version is None:
        new_version = incr_dispatch(
            old_version,
            raw_pattern=raw_pattern,
            major=major,
            minor=minor,
            patch=patch,
            tag=tag,
            tag_num=tag_num,
            pin_date=pin_date,
            date=_date,
        )
    else:
        new_version = set_version

    if new_version is None:
        _log_no_change('test', raw_pattern)
        sys.exit(1)

    if not _is_valid_version(raw_pattern, old_version, new_version):
        if set_version:
            logger.error(f"Invalid argument --set-version='{set_version}'")

        sys.exit(1)

    pep440_version = version.to_pep440(new_version)

    click.echo(f"New Version: {new_version}")
    if new_version != pep440_version:
        click.echo(f"PEP440     : {pep440_version}")


def _grep_text(pattern: patterns.Pattern, text: str, color: bool) -> typ.Iterable[str]:
    all_lines = text.splitlines()
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

        prefixed_lines = [f"{lines_offset + i:>4}: {line}" for i, line in enumerate(lines)]
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
            if len(file_ios) > 1:
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
@verbose_option
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

    raw_pattern        = pattern  # use internal naming convention
    normalized_pattern = _get_normalized_pattern(raw_pattern, version_pattern)

    isatty = getattr(sys.stdout, 'isatty', lambda: False)

    if isatty():
        colorama.init()
        try:
            _grep(normalized_pattern, files, color=True)
        finally:
            colorama.deinit()
    else:
        _grep(normalized_pattern, files, color=False)


@cli.command()
@verbose_option
@fetch_option
@env_option
def show(verbose: int = 0, fetch: bool = True, env: bool = False) -> None:
    """Show current version of your project."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    _, cfg = config.init(project_path=".")

    if cfg is None:
        logger.error("Could not parse configuration. Perhaps try 'bumpver init'.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)
    if env:
        version_info = v2version.parse_version_info(cfg.current_version, cfg.version_pattern)
        for key, val in version_info._asdict().items():
            click.echo(f"{key.upper()}={val if val else ''}")
        click.echo(f"CURRENT_VERSION={cfg.current_version}")
        click.echo(f"PEP440_VERSION={cfg.pep440_version}")
    else:
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


def _v2_get_diff(cfg: config.Config, new_version: str) -> str:
    old_vinfo = v2version.parse_version_info(cfg.current_version, cfg.version_pattern)
    new_vinfo = v2version.parse_version_info(new_version, cfg.version_pattern)
    return v2rewrite.diff(old_vinfo, new_vinfo, cfg.file_patterns)


def _v1_get_diff(cfg: config.Config, new_version: str) -> str:
    old_vinfo = v1version.parse_version_info(cfg.current_version, cfg.version_pattern)
    new_vinfo = v1version.parse_version_info(new_version, cfg.version_pattern)
    return v1rewrite.diff(old_vinfo, new_vinfo, cfg.file_patterns)


def get_diff(cfg, new_version) -> str:
    if cfg.is_new_pattern:
        return _v2_get_diff(cfg, new_version)
    else:
        return _v1_get_diff(cfg, new_version)


def _print_diff_str(diff: str) -> None:
    colored_diff = "\n".join(_colored_diff_lines(diff))
    if sys.stdout.isatty():
        click.echo(colored_diff)
    else:
        click.echo(diff)


def _print_diff(cfg: config.Config, new_version: str) -> None:
    try:
        diff = get_diff(cfg, new_version)
        _print_diff_str(diff)
    except OSError as err:
        logger.error(str(err))
        sys.exit(1)
    except rewrite.NoPatternMatch as ex:
        logger.error(str(ex))
        sys.exit(1)


def _is_valid_version(raw_pattern: str, old_version: str, new_version: str) -> bool:
    is_new_pattern = "{" not in raw_pattern and "}" not in raw_pattern
    try:
        if is_new_pattern:
            v2version.parse_version_info(new_version, raw_pattern)
        else:
            v1version.parse_version_info(new_version, raw_pattern)
    except version.PatternError:
        logger.error(f"Invalid version '{new_version}' for pattern '{raw_pattern}'")
        return False

    if version.parse_version(new_version) <= version.parse_version(old_version):
        logger.error("Invariant violated: New version must be greater than old version ")
        logger.error(f"  Failed Invariant: '{new_version}' > '{old_version}'")
        return False
    else:
        return True


def incr_dispatch(
    old_version: str,
    raw_pattern: str,
    *,
    major   : bool = False,
    minor   : bool = False,
    patch   : bool = False,
    tag     : str = None,
    tag_num : bool = False,
    pin_date: bool = False,
    date    : typ.Optional[dt.date] = None,
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
            major=major,
            minor=minor,
            patch=patch,
            tag=tag,
            tag_num=tag_num,
            pin_date=pin_date,
            date=date,
        )
    else:
        return v2version.incr(
            old_version,
            raw_pattern=raw_pattern,
            major=major,
            minor=minor,
            patch=patch,
            tag=tag,
            tag_num=tag_num,
            pin_date=pin_date,
            date=date,
        )


def _update(
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


def _try_update(
    cfg           : config.Config,
    new_version   : str,
    commit_message: str,
    allow_dirty   : bool = False,
) -> None:
    try:
        _update(cfg, new_version, commit_message, allow_dirty)
    except sp.CalledProcessError as ex:
        logger.error(f"Error running subcommand: {ex.cmd}")
        if ex.stdout:
            sys.stdout.write(ex.stdout.decode('utf-8'))
        if ex.stderr:
            sys.stderr.write(ex.stderr.decode('utf-8'))
        sys.exit(1)


@cli.command()
@verbose_option
@dry_option
def init(verbose: int = 0, dry: bool = False) -> None:
    """Initialize [bumpver] configuration."""
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


def get_latest_vcs_version_tag(cfg: config.Config, fetch: bool) -> typ.Optional[str]:
    all_tags = vcs.get_tags(fetch=fetch)

    if cfg.is_new_pattern:
        version_tags = [tag for tag in all_tags if v2version.is_valid(tag, cfg.version_pattern)]
    else:
        version_tags = [tag for tag in all_tags if v1version.is_valid(tag, cfg.version_pattern)]

    if version_tags:
        version_tags.sort(key=version.parse_version, reverse=True)
        _debug_tags = ", ".join(version_tags[:3])
        logger.debug(f"found tags: {_debug_tags} ... ({len(version_tags)} in total)")
        return version_tags[0]
    else:
        return None


def _update_cfg_from_vcs(cfg: config.Config, fetch: bool) -> config.Config:
    latest_version_tag = get_latest_vcs_version_tag(cfg, fetch)
    if latest_version_tag is None:
        logger.debug("no vcs tags found")
        return cfg
    else:
        latest_version_pep440 = version.to_pep440(latest_version_tag)
        if latest_version_tag <= cfg.current_version:
            # current_version already newer/up-to-date
            return cfg
        else:
            logger.info(f"Working dir version        : {cfg.current_version}")
            logger.info(f"Latest version from VCS tag: {latest_version_tag}")
            return cfg._replace(
                current_version=latest_version_tag,
                pep440_version=latest_version_pep440,
            )


@cli.command()
@dry_option
@fetch_option
@verbose_option
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
@version_options
def update(
    dry        : bool = False,
    allow_dirty: bool = False,
    fetch      : bool = True,
    verbose    : int = 0,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
    tag        : typ.Optional[str] = None,
    tag_num    : bool = False,
    pin_date   : bool = False,
    date       : typ.Optional[str] = None,
    set_version: typ.Optional[str] = None,
) -> None:
    """Update project files with the incremented version string."""
    verbose = max(_VERBOSE, verbose)
    _configure_logging(verbose)
    _validate_release_tag(tag)
    _date = _validate_date(date, pin_date)

    _, cfg = config.init(project_path=".")

    if cfg is None:
        logger.error("Could not parse configuration.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)

    old_version = cfg.current_version
    if set_version is None:
        new_version = incr_dispatch(
            old_version,
            raw_pattern=cfg.version_pattern,
            major=major,
            minor=minor,
            patch=patch,
            tag=tag,
            tag_num=tag_num,
            pin_date=pin_date,
            date=_date,
        )
    else:
        new_version = set_version

    if new_version is None:
        _log_no_change('update', cfg.version_pattern)
        sys.exit(1)

    if not _is_valid_version(cfg.version_pattern, old_version, new_version):
        if set_version:
            logger.error(f"Invalid argument --set-version='{set_version}'")

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

    _try_update(cfg, new_version, commit_message, allow_dirty)


if __name__ == '__main__':
    cli()
