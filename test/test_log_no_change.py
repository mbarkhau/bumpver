# -*- coding: utf-8 -*-
"""Tests for the semver hint in bumpver test/show when nothing changed."""
import logging

from bumpver import cli


def test_log_no_change_partial_pattern_suggests_flags(caplog):
    """A MAJOR.PATCH pattern (no MINOR) is not SemVer: suggest its flags."""
    with caplog.at_level(logging.INFO, logger="bumpver.cli"):
        cli._log_no_change("test", "vMAJOR.PATCH")
    assert "--major/--patch" in caplog.text


def test_log_no_change_full_semver_warns(caplog):
    """A MAJOR.MINOR.PATCH pattern warns that an increment flag is required."""
    with caplog.at_level(logging.INFO, logger="bumpver.cli"):
        cli._log_no_change("test", "vMAJOR.MINOR.PATCH")
    assert "required for use with SemVer" in caplog.text
