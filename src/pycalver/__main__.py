#!/usr/bin/env python
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import io
import os
import sys
import click
import logging
import typing as typ

from . import DEBUG
from . import vcs
from . import parse
from . import config
from . import version
from . import rewrite


log = logging.getLogger("pycalver.__main__")


def _init_loggers(verbose: bool) -> None:
    if DEBUG:
        log_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        log_level = logging.DEBUG
    elif verbose:
        log_formatter = logging.Formatter('%(levelname)s - %(message)s')
        log_level = logging.INFO
    else:
        log_formatter = logging.Formatter('%(message)s')
        log_level = logging.WARNING

    loggers = [log, vcs.log, parse.log, config.log, rewrite.log, version.log]

    for logger in loggers:
        if len(logger.handlers) == 0:
            ch = logging.StreamHandler(sys.stderr)
            ch.setFormatter(log_formatter)
            logger.addHandler(ch)
            logger.setLevel(log_level)

    log.debug("Loggers initialized.")


@click.group()
def cli():
    """parse and update project versions automatically."""


@cli.command()
def show() -> None:
    _init_loggers(verbose=False)

    cfg = config.parse()
    if cfg is None:
        return

    print(f"Current Version: {cfg['current_version']}")
    print(f"PEP440 Version: {cfg['pep440_version']}")


@cli.command()
@click.option(
    "--dry",
    default=False,
    is_flag=True,
    help="Display diff of changes, don't rewrite files.",
)
def init(dry: bool) -> None:
    """Initialize [pycalver] configuration in setup.cfg"""
    _init_loggers(verbose=False)

    cfg = config.parse()
    if cfg:
        log.error("Configuration already initialized in setup.cfg")
        return

    cfg_lines = config.default_config_lines()

    if dry:
        print("Exiting because of '--dry'. Would have written to setup.cfg:")
        print("\n    " + "\n    ".join(cfg_lines))
        return

    if os.path.exists("setup.cfg"):
        cfg_content = "\n" + "\n".join(cfg_lines)
        with io.open("setup.cfg", mode="at", encoding="utf-8") as fh:
            fh.write(cfg_content)
        print("Updated setup.cfg")
    else:
        cfg_content = "\n".join(cfg_lines)
        with io.open("setup.cfg", mode="at", encoding="utf-8") as fh:
            fh.write(cfg_content)
        print("Created setup.cfg")


@cli.command()
@click.option(
    "--verbose",
    default=False,
    is_flag=True,
    help="Log applied changes to stderr",
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
    help="Override release name of current_version",
)
def bump(verbose: bool, dry: bool, release: typ.Optional[str] = None) -> None:
    _init_loggers(verbose)
    if release and release not in parse.VALID_RELESE_VALUES:
        log.error(f"Invalid argument --release={release}")
        log.error(f"Valid arguments are: {', '.join(parse.VALID_RELESE_VALUES)}")
        return

    cfg = config.parse()

    if cfg is None:
        log.error("Unable to parse pycalver configuration from setup.cfg")
        return

    old_version = cfg["current_version"]
    new_version = version.bump(old_version, release=release)

    log.info(f"Old Version: {old_version}")
    log.info(f"New Version: {new_version}")

    matches: typ.List[parse.PatternMatch]
    for filepath, patterns in cfg["file_patterns"].items():
        with io.open(filepath, mode="rt", encoding="utf-8") as fh:
            content = fh.read()
        lines = content.splitlines()
        matches = parse.parse_patterns(lines, patterns)
        for m in matches:
            print(m)
