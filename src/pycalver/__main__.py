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
import sys
import typing as typ
import logging
import subprocess as sp

import click

import pycalver.cli as v1cli
import pycalver.version as v1version
import pycalver2.version as v2version
from pycalver import vcs
from pycalver import config

# import pycalver2.cli as v2cli

_VERBOSE = 0


try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


click.disable_unicode_literals_warning = True

logger = logging.getLogger("pycalver.__main__")


def _configure_logging(verbose: int = 0) -> None:
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


VALID_RELEASE_VALUES = ("alpha", "beta", "dev", "rc", "post", "final")


def _validate_release_tag(release: str) -> None:
    if release in VALID_RELEASE_VALUES:
        return

    logger.error(f"Invalid argument --release={release}")
    logger.error(f"Valid arguments are: {', '.join(VALID_RELEASE_VALUES)}")
    sys.exit(1)


@click.group()
@click.version_option(version="v202007.0036")
@click.help_option()
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
def cli(verbose: int = 0) -> None:
    """Automatically update PyCalVer version strings on python projects."""
    # pylint:disable=global-statement; global flag is global.
    global _VERBOSE
    _VERBOSE = verbose


@cli.command()
@click.argument("old_version")
@click.argument("pattern", default="{pycalver}")
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
@click.option(
    "--release", default=None, metavar="<name>", help="Override release name of current_version"
)
@click.option("--major", is_flag=True, default=False, help="Increment major component.")
@click.option("--minor", is_flag=True, default=False, help="Increment minor component.")
@click.option("--patch", is_flag=True, default=False, help="Increment patch component.")
def test(
    old_version: str,
    pattern    : str  = "{pycalver}",
    verbose    : int  = 0,
    release    : str  = None,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
) -> None:
    """Increment a version number for demo purposes."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    if release:
        _validate_release_tag(release)

    new_version = _incr(
        old_version,
        pattern=pattern,
        release=release,
        major=major,
        minor=minor,
        patch=patch,
    )
    if new_version is None:
        logger.error(f"Invalid version '{old_version}' and/or pattern '{pattern}'.")
        sys.exit(1)

    # TODO (mb 2020-09-05): version switch
    pep440_version = v1version.to_pep440(new_version)
    # pep440_version = v2version.to_pep440(new_version)

    click.echo(f"New Version: {new_version}")
    click.echo(f"PEP440     : {pep440_version}")


@cli.command()
@click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
@click.option(
    "-f/-n", "--fetch/--no-fetch", is_flag=True, default=True, help="Sync tags from remote origin."
)
def show(verbose: int = 0, fetch: bool = True) -> None:
    """Show current version of your project."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    ctx: config.ProjectContext = config.init_project_ctx(project_path=".")
    cfg: config.MaybeConfig    = config.parse(ctx)

    if cfg is None:
        logger.error("Could not parse configuration. Perhaps try 'pycalver init'.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)
    click.echo(f"Current Version: {cfg.current_version}")
    click.echo(f"PEP440         : {cfg.pep440_version}")


def _try_print_diff(cfg: config.Config, new_version: str) -> None:
    try:
        # TODO (mb 2020-09-05): version switch
        diff = v1cli.get_diff(cfg, new_version)
        # diff = v2cli.get_diff(cfg, new_version)

        if sys.stdout.isatty():
            for line in diff.splitlines():
                if line.startswith("+++") or line.startswith("---"):
                    click.echo(line)
                elif line.startswith("+"):
                    click.echo("\u001b[32m" + line + "\u001b[0m")
                elif line.startswith("-"):
                    click.echo("\u001b[31m" + line + "\u001b[0m")
                elif line.startswith("@"):
                    click.echo("\u001b[36m" + line + "\u001b[0m")
                else:
                    click.echo(line)
        else:
            click.echo(diff)
    except Exception as ex:
        # pylint:disable=broad-except; Mostly we expect IOError here, but
        #   could be other things and there's no option to recover anyway.
        logger.error(str(ex), exc_info=True)
        sys.exit(1)


def _incr(
    old_version: str,
    pattern    : str = "{pycalver}",
    *,
    release: str  = None,
    major  : bool = False,
    minor  : bool = False,
    patch  : bool = False,
) -> typ.Optional[str]:
    is_v1_pattern = "{" in pattern
    if is_v1_pattern:
        return v1version.incr(
            old_version,
            pattern=pattern,
            release=release,
            major=major,
            minor=minor,
            patch=patch,
        )
    else:
        return v2version.incr(
            old_version,
            pattern=pattern,
            release=release,
            major=major,
            minor=minor,
            patch=patch,
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
            logger.warning("Version Control System not found, aborting commit.")

    filepaths = set(cfg.file_patterns.keys())

    if vcs_api:
        vcs.assert_not_dirty(vcs_api, filepaths, allow_dirty)

    try:
        # TODO (mb 2020-09-05): version switch
        v1cli.rewrite(cfg, new_version)
        # v2cli.rewrite(cfg, new_version)
    except Exception as ex:
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
    "--dry", default=False, is_flag=True, help="Display diff of changes, don't rewrite files."
)
def init(verbose: int = 0, dry: bool = False) -> None:
    """Initialize [pycalver] configuration."""
    _configure_logging(verbose=max(_VERBOSE, verbose))

    ctx: config.ProjectContext = config.init_project_ctx(project_path=".")
    cfg: config.MaybeConfig    = config.parse(ctx)

    if cfg:
        logger.error(f"Configuration already initialized in {ctx.config_filepath}")
        sys.exit(1)

    if dry:
        click.echo(f"Exiting because of '--dry'. Would have written to {ctx.config_filepath}:")
        cfg_text: str = config.default_config(ctx)
        click.echo("\n    " + "\n    ".join(cfg_text.splitlines()))
        sys.exit(0)

    config.write_content(ctx)


def _update_cfg_from_vcs(cfg: config.Config, fetch: bool) -> config.Config:
    all_tags = vcs.get_tags(fetch=fetch)

    # TODO (mb 2020-09-05): version switch
    cfg = v1cli.update_cfg_from_vcs(cfg, all_tags)
    # cfg = v2cli.update_cfg_from_vcs(cfg, all_tags)
    return cfg


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
    "--dry",
    default=False,
    is_flag=True,
    help="Display diff of changes, don't rewrite files.",
)
@click.option(
    "--release",
    default=None,
    metavar="<name>",
    help=(
        f"Override release name of current_version. Valid options are: "
        f"{', '.join(VALID_RELEASE_VALUES)}."
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
@click.option("--minor", is_flag=True, default=False, help="Increment minor component.")
@click.option("--patch", is_flag=True, default=False, help="Increment patch component.")
def bump(
    release    : typ.Optional[str] = None,
    verbose    : int  = 0,
    dry        : bool = False,
    allow_dirty: bool = False,
    fetch      : bool = True,
    major      : bool = False,
    minor      : bool = False,
    patch      : bool = False,
) -> None:
    """Increment the current version string and update project files."""
    verbose = max(_VERBOSE, verbose)
    _configure_logging(verbose)

    if release:
        _validate_release_tag(release)

    ctx: config.ProjectContext = config.init_project_ctx(project_path=".")
    cfg: config.MaybeConfig    = config.parse(ctx)

    if cfg is None:
        logger.error("Could not parse configuration. Perhaps try 'pycalver init'.")
        sys.exit(1)

    cfg = _update_cfg_from_vcs(cfg, fetch)

    old_version = cfg.current_version
    new_version = _incr(
        old_version,
        pattern=cfg.version_pattern,
        release=release,
        major=major,
        minor=minor,
        patch=patch,
    )

    if new_version is None:
        is_semver      = "{semver}" in cfg.version_pattern
        has_semver_inc = major or minor or patch
        if is_semver and not has_semver_inc:
            logger.warning("bump --major/--minor/--patch required when using semver.")
        else:
            logger.error(f"Invalid version '{old_version}' and/or pattern '{cfg.version_pattern}'.")
        sys.exit(1)

    logger.info(f"Old Version: {old_version}")
    logger.info(f"New Version: {new_version}")

    if dry or verbose >= 2:
        _try_print_diff(cfg, new_version)

    if dry:
        return

    # # TODO (mb 2020-09-05): format from config
    # commit_message_kwargs = {
    #     new_version
    #     old_version
    #     pep440_new_version
    #     pep440_old_version
    # }
    # cfg.commit_message =
    commit_message = f"bump version to {new_version}"

    _try_bump(cfg, new_version, commit_message, allow_dirty)


if __name__ == '__main__':
    cli()
