# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import io
import os
import re
import time
import shlex
import shutil
import datetime as dt
import subprocess as sp

import pytest
import pathlib2 as pl
from click.testing import CliRunner

from pycalver import v1cli
from pycalver import v2cli
from pycalver import config
from pycalver import v1patterns
from pycalver.__main__ import cli
from pycalver.__main__ import incr_dispatch

# pylint:disable=redefined-outer-name ; pytest fixtures
# pylint:disable=protected-access ; allowed for test code


README_TEXT_FIXTURE = """
        Hello World v201701.1002-alpha !
        [aka. 201701.1002a0 !]
"""


SETUP_CFG_FIXTURE = """
[metadata]
license_file = LICENSE

[bdist_wheel]
universal = 1
"""

PYCALVER_TOML_FIXTURE = """
"""

PYPROJECT_TOML_FIXTURE = """
[build-system]
requires = ["setuptools", "wheel"]
"""

ENV = {
    'GIT_AUTHOR_NAME'    : "pycalver_tester",
    'GIT_COMMITTER_NAME' : "pycalver_tester",
    'GIT_AUTHOR_EMAIL'   : "pycalver_tester@nowhere.com",
    'GIT_COMMITTER_EMAIL': "pycalver_tester@nowhere.com",
    'HGUSER'             : "pycalver_tester",
    'PATH'               : os.environ['PATH'],
}


def shell(*cmd):
    return sp.check_output(cmd, env=ENV)


@pytest.fixture
def runner(tmpdir):
    runner   = CliRunner(env=ENV)
    orig_cwd = os.getcwd()

    _debug = 0
    if _debug:
        tmpdir = pl.Path("..") / "tmp_test_pycalver_project"
        if tmpdir.exists():
            time.sleep(0.2)
            shutil.rmtree(str(tmpdir))
        tmpdir.mkdir()

    os.chdir(str(tmpdir))

    yield runner

    os.chdir(orig_cwd)

    if not _debug:
        shutil.rmtree(str(tmpdir))


def test_help(runner):
    result = runner.invoke(cli, ['--help', "-vv"])
    assert result.exit_code == 0
    assert "PyCalVer" in result.output
    assert "bump " in result.output
    assert "test " in result.output
    assert "init " in result.output
    assert "show " in result.output


def test_version(runner):
    result = runner.invoke(cli, ['--version', "-vv"])
    assert result.exit_code == 0
    assert " version v20" in result.output
    match = v1patterns.PYCALVER_RE.search(result.output)
    assert match


def test_incr_default(runner):
    old_version = "v201701.0004-alpha"

    cmd    = ['test', "-vv", "--pin-date", "--release", "beta", old_version]
    result = runner.invoke(cli, cmd)
    assert result.exit_code == 0
    assert "Version: v201701.0005-beta\n" in result.output

    cmd    = ['test', "-vv", "--pin-date", "--release", "beta", old_version, "vYYYY0M.BUILD[-RELEASE]"]
    result = runner.invoke(cli, cmd)
    assert result.exit_code == 0
    assert "Version: v201701.1005-beta\n" in result.output


def test_incr_pin_date(runner):
    old_version = "v201701.0999-alpha"
    result      = runner.invoke(cli, ['test', "-vv", "--pin-date", old_version])
    assert result.exit_code == 0
    assert "Version: v201701.11000-alpha\n" in result.output


def test_incr_semver(runner):
    semver_patterns = [
        "{semver}",
        "{MAJOR}.{MINOR}.{PATCH}",
        "MAJOR.MINOR.PATCH",
    ]

    for semver_pattern in semver_patterns:
        old_version = "0.1.0"
        new_version = "0.1.1"

        result = runner.invoke(cli, ['test', "-vv", "--patch", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output

        old_version = "0.1.1"
        new_version = "0.2.0"

        result = runner.invoke(cli, ['test', "-vv", "--minor", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output

        old_version = "0.1.1"
        new_version = "1.0.0"

        result = runner.invoke(cli, ['test', "-vv", "--major", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output


def test_incr_semver_invalid(runner, caplog):
    result = runner.invoke(cli, ['test', "-vv", "--patch", "0.1.1"])
    assert result.exit_code == 1
    assert len(caplog.records) > 0
    log_record = caplog.records[0]
    assert "Invalid version string" in log_record.message
    assert "for pattern '{pycalver}'" in log_record.message


def test_incr_to_beta(runner):
    old_version     = "v201701.0999-alpha"
    initial_version = config._initial_version()

    result = runner.invoke(cli, ['test', old_version, "-vv", "--release", "beta"])
    assert result.exit_code == 0
    new_version = initial_version.replace(".1001-alpha", ".11000-beta")
    assert f"Version: {new_version}\n" in result.output


def test_incr_to_final(runner):
    old_version     = "v201701.0999-alpha"
    initial_version = config._initial_version()

    result = runner.invoke(cli, ['test', old_version, "-vv", "--release", "final"])
    assert result.exit_code == 0
    new_version = initial_version.replace(".1001-alpha", ".11000")
    assert f"Version: {new_version}\n" in result.output


def test_incr_release_num(runner):
    semver = "MAJOR.MINOR.PATCH[PYTAGNUM]"

    old_version = "0.1.0b0"
    new_version = "0.1.0b1"

    result = runner.invoke(cli, ['test', "-vv", "--release-num", old_version, semver])
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


def test_incr_invalid(runner):
    old_version = "v201701.0999-alpha"

    result = runner.invoke(cli, ['test', old_version, "-vv", "--release", "alfa"])
    assert result.exit_code == 1


def _add_project_files(*files):
    if "README.md" in files:
        with pl.Path("README.md").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(README_TEXT_FIXTURE)

    if "setup.cfg" in files:
        with pl.Path("setup.cfg").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(SETUP_CFG_FIXTURE)

    if "pycalver.toml" in files:
        with pl.Path("pycalver.toml").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(PYCALVER_TOML_FIXTURE)

    if "pyproject.toml" in files:
        with pl.Path("pyproject.toml").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(PYPROJECT_TOML_FIXTURE)


def _update_config_val(filename, **kwargs):
    with io.open(filename, mode="r", encoding="utf-8") as fobj:
        old_cfg_text = fobj.read()

    new_cfg_text = old_cfg_text
    for key, val in kwargs.items():
        replacement = "{} = {}".format(key, val)
        if replacement not in new_cfg_text:
            pattern      = r"^{} = .*$".format(key)
            new_cfg_text = re.sub(pattern, replacement, new_cfg_text, flags=re.MULTILINE)
            assert old_cfg_text != new_cfg_text

    with io.open(filename, mode="w", encoding="utf-8") as fobj:
        fobj.write(new_cfg_text)


def test_nocfg(runner, caplog):
    _add_project_files("README.md")
    result = runner.invoke(cli, ['show', "-vv"])
    assert result.exit_code == 1
    expected_msg = "Could not parse configuration. Perhaps try 'pycalver init'."
    assert any(expected_msg in r.message for r in caplog.records)


def test_novcs_nocfg_init(runner, caplog):
    _add_project_files("README.md")
    # dry mode test
    result = runner.invoke(cli, ['init', "-vv", "--dry"])
    assert result.exit_code == 0
    assert not os.path.exists("pycalver.toml")

    # check logging
    assert len(caplog.records) == 1
    log = caplog.records[0]
    assert log.levelname == 'WARNING'
    assert "File not found" in log.message

    # non dry mode
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    # check logging
    assert len(caplog.records) == 2
    log = caplog.records[1]
    assert log.levelname == 'WARNING'
    assert "File not found" in log.message

    assert os.path.exists("pycalver.toml")
    with pl.Path("pycalver.toml").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_TOML_BASE_TMPL.format(initial_version=config._initial_version())
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 1

    # check logging
    assert len(caplog.records) == 3
    log = caplog.records[2]
    assert log.levelname == 'ERROR'
    assert "Configuration already initialized" in log.message


def test_novcs_setupcfg_init(runner):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_CONFIGPARSER_BASE_TMPL.format(
        initial_version=config._initial_version()
    )
    assert base_str                                  in cfg_content
    assert config.DEFAULT_CONFIGPARSER_README_MD_STR in cfg_content

    result = runner.invoke(cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_novcs_pyproject_init(runner):
    _add_project_files("README.md", "pyproject.toml")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("pyproject.toml").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_TOML_BASE_TMPL.format(initial_version=config._initial_version())
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def _vcs_init(vcs, files=("README.md",)):
    assert vcs in ("git", "hg")
    assert not pl.Path(f".{vcs}").exists()
    shell(f"{vcs}", "init")
    assert pl.Path(f".{vcs}").is_dir()

    for filename in files:
        shell(f"{vcs}", "add", filename)

    shell(f"{vcs}", "commit", "-m", "initial commit")


DEFAULT_VERSION_PATTERNS = [
    '"{pycalver}"',
    '"vYYYY0M.BUILD[-RELEASE]"',
]


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_git_init(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_hg_init(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_v1_git_tag_eval(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("git")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    initial_version    = config._initial_version()
    tag_version        = initial_version.replace(".1001-alpha", ".1123-beta")
    tag_version_pep440 = tag_version[1:7] + ".1123b0"

    shell("git", "tag", "--annotate", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output
    assert f"PEP440         : {tag_version_pep440}\n" in result.output


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_hg_tag_eval(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("hg")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    initial_version    = config._initial_version()
    tag_version        = initial_version.replace(".1001-alpha", ".1123-beta")
    tag_version_pep440 = tag_version[1:7] + ".1123b0"

    shell("hg", "tag", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output
    assert f"PEP440         : {tag_version_pep440}\n" in result.output


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_novcs_bump(runner, version_pattern):
    _add_project_files("README.md")

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    result = runner.invoke(cli, ['bump', "-vv"])
    assert result.exit_code == 0

    calver = config._initial_version().split(".")[0]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content
        assert calver[1:] + ".1002a0 !]\n" in content

    result = runner.invoke(cli, ['bump', "-vv", "--release", "beta"])
    assert result.exit_code == 0

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1003-beta !\n" in content
        assert calver[1:] + ".1003b0 !]\n" in content


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_git_bump(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    shell("git", "add", "pycalver.toml")
    shell("git", "commit", "-m", "initial commit")

    result = runner.invoke(cli, ['bump', "-vv"])
    assert result.exit_code == 0

    calver = config._initial_version()[:7]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_hg_bump(runner, version_pattern):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("pycalver.toml", version_pattern=version_pattern)

    shell("hg", "add", "pycalver.toml")
    shell("hg", "commit", "-m", "initial commit")

    result = runner.invoke(cli, ['bump', "-vv"])
    assert result.exit_code == 0

    calver = config._initial_version()[:7]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content


def test_empty_git_bump(runner, caplog):
    shell("git", "init")
    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write("")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fobj:
        default_cfg_data = fobj.read()

    assert "[pycalver]\n" in default_cfg_data
    assert "\ncurrent_version = " in default_cfg_data
    assert "\n[pycalver:file_patterns]\n" in default_cfg_data
    assert "\nsetup.cfg =\n" in default_cfg_data

    result = runner.invoke(cli, ['bump'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)


def test_empty_hg_bump(runner, caplog):
    shell("hg", "init")
    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write("")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fobj:
        default_cfg_text = fobj.read()

    assert "[pycalver]\n" in default_cfg_text
    assert "\ncurrent_version = " in default_cfg_text
    assert "\n[pycalver:file_patterns]\n" in default_cfg_text
    assert "\nsetup.cfg =\n" in default_cfg_text

    result = runner.invoke(cli, ['bump'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)


SETUP_CFG_SEMVER_FIXTURE = """
[metadata]
license_file = LICENSE

[bdist_wheel]
universal = 1

[pycalver]
current_version = "0.1.0"
version_pattern = "{semver}"

[pycalver:file_patterns]
setup.cfg =
    current_version = "{version}"
"""


DEFAULT_SEMVER_PATTERNS = [
    '"{semver}"',
    '"MAJOR.MINOR.PATCH"',
]


@pytest.mark.parametrize("version_pattern", DEFAULT_SEMVER_PATTERNS)
def test_v1_bump_semver_warning(runner, caplog, version_pattern):
    _add_project_files("README.md")

    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write(SETUP_CFG_SEMVER_FIXTURE)

    _update_config_val("setup.cfg", version_pattern=version_pattern)

    _vcs_init("hg", files=["README.md", "setup.cfg"])

    result = runner.invoke(cli, ['bump', "-vv", "-n", "--dry"])
    assert result.exit_code == 1

    assert any("version did not change" in r.message for r in caplog.records)
    assert any("--major/--minor/--patch required" in r.message for r in caplog.records)

    result = runner.invoke(cli, ['bump', "-vv", "-n", "--dry", "--patch"])
    assert result.exit_code == 0


@pytest.mark.parametrize("version_pattern", DEFAULT_SEMVER_PATTERNS)
def test_v1_bump_semver_diff(runner, caplog, version_pattern):
    _add_project_files("README.md")

    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write(SETUP_CFG_SEMVER_FIXTURE)

    _update_config_val("setup.cfg", version_pattern=version_pattern)

    _vcs_init("hg", files=["README.md", "setup.cfg"])

    cases = [("--major", "1.0.0"), ("--minor", "0.2.0"), ("--patch", "0.1.1")]

    for flag, expected in cases:
        result = runner.invoke(cli, ['bump', "-vv", "-n", "--dry", flag])
        assert result.exit_code == 0
        assert len(caplog.records) == 0

        out_lines = set(result.output.splitlines())

        assert "+++ setup.cfg" in out_lines
        assert "-current_version = \"0.1.0\"" in out_lines
        assert f"+current_version = \"{expected}\"" in out_lines


@pytest.mark.parametrize("version_pattern", DEFAULT_VERSION_PATTERNS)
def test_get_diff(runner, version_pattern):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("setup.cfg", version_pattern=version_pattern)

    _, cfg = config.init()
    new_version = "v202010.1003-beta"

    if cfg.is_new_pattern:
        diff_str = v2cli.get_diff(cfg, new_version)
    else:
        diff_str = v1cli.get_diff(cfg, new_version)

    diff_lines = set(diff_str.splitlines())

    assert "-        Hello World v201701.1002-alpha !" in diff_lines
    assert "-        [aka. 201701.1002a0 !]" in diff_lines
    assert "+        Hello World v202010.1003-beta !" in diff_lines
    assert "+        [aka. 202010.1003b0 !]" in diff_lines

    assert '-current_version = "v202010.1001-alpha"' in diff_lines
    assert '+current_version = "v202010.1003-beta"' in diff_lines


WEEKNUM_TEST_CASES = [
    # 2020-12-26  Sat
    ("2020-12-26", "YYYY.0W", "2020.51"),
    ("2020-12-26", "YYYY.0U", "2020.51"),
    ("2020-12-26", "GGGG.0V", "2020.52"),
    # 2020-12-27  Sun
    ("2020-12-27", "YYYY.0W", "2020.51"),
    ("2020-12-27", "YYYY.0U", "2020.52"),
    ("2020-12-27", "GGGG.0V", "2020.52"),
    # 2020-12-28  Mon
    ("2020-12-28", "YYYY.0W", "2020.52"),
    ("2020-12-28", "YYYY.0U", "2020.52"),
    ("2020-12-28", "GGGG.0V", "2020.53"),
    # 2020-12-29  Tue
    ("2020-12-29", "YYYY.0W", "2020.52"),
    ("2020-12-29", "YYYY.0U", "2020.52"),
    ("2020-12-29", "GGGG.0V", "2020.53"),
    # 2020-12-30  Wed
    ("2020-12-30", "YYYY.0W", "2020.52"),
    ("2020-12-30", "YYYY.0U", "2020.52"),
    ("2020-12-30", "GGGG.0V", "2020.53"),
    # 2020-12-31  Thu
    ("2020-12-31", "YYYY.0W", "2020.52"),
    ("2020-12-31", "YYYY.0U", "2020.52"),
    ("2020-12-31", "GGGG.0V", "2020.53"),
    # 2021-01-01  Fri
    ("2021-01-01", "YYYY.0W", "2021.00"),
    ("2021-01-01", "YYYY.0U", "2021.00"),
    ("2021-01-01", "GGGG.0V", "2020.53"),
    # 2021-01-02  Sat
    ("2021-01-02", "YYYY.0W", "2021.00"),
    ("2021-01-02", "YYYY.0U", "2021.00"),
    ("2021-01-02", "GGGG.0V", "2020.53"),
    # 2021-01-03  Sun
    ("2021-01-03", "YYYY.0W", "2021.00"),
    ("2021-01-03", "YYYY.0U", "2021.01"),
    ("2021-01-03", "GGGG.0V", "2020.53"),
    # 2021-01-04  Mon
    ("2021-01-04", "YYYY.0W", "2021.01"),
    ("2021-01-04", "YYYY.0U", "2021.01"),
    ("2021-01-04", "GGGG.0V", "2021.01"),
]


@pytest.mark.parametrize("date, pattern, expected", WEEKNUM_TEST_CASES)
def test_weeknum(date, pattern, expected, runner):
    cmd    = shlex.split(f"test -vv --date {date} 2020.40 {pattern}")
    result = runner.invoke(cli, cmd)
    assert result.exit_code == 0
    assert "New Version: " + expected in result.output


def test_hg_commit_message(runner, caplog):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    commit_message = """
    "bump from {old_version} ({old_version_pep440}) to {new_version} ({new_version_pep440})"
    """
    _update_config_val("setup.cfg", current_version='"v201903.1001-alpha"')
    _update_config_val("setup.cfg", commit_message=commit_message.strip())

    _vcs_init("hg", ["README.md", "setup.cfg"])
    assert len(caplog.records) > 0

    result = runner.invoke(cli, ['bump', "-vv", "--pin-date", "--release", "beta"])
    assert result.exit_code == 0

    tags = shell("hg", "tags").decode("utf-8")
    assert "v201903.1002-beta" in tags

    commits = shell(*shlex.split("hg log -l 2")).decode("utf-8").split("\n\n")

    expected = "bump from v201903.1001-alpha (201903.1001a0) to v201903.1002-beta (201903.1002b0)"
    summary  = commits[1].split("summary:")[-1]
    assert expected in summary


def test_git_commit_message(runner, caplog):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli, ['init', "-vv"])
    assert result.exit_code == 0

    commit_message = """
    "bump: {old_version} ({old_version_pep440}) -> {new_version} ({new_version_pep440})"
    """
    _update_config_val("setup.cfg", current_version='"v201903.1001-alpha"')
    _update_config_val("setup.cfg", commit_message=commit_message.strip())

    _vcs_init("git", ["README.md", "setup.cfg"])
    assert len(caplog.records) > 0

    result = runner.invoke(cli, ['bump', "-vv", "--pin-date", "--release", "beta"])
    assert result.exit_code == 0

    tags = shell("git", "tag", "--list").decode("utf-8")
    assert "v201903.1002-beta" in tags

    commits = shell(*shlex.split("git log -l 2")).decode("utf-8").split("\n\n")

    expected = "bump: v201903.1001-alpha (201903.1001a0) -> v201903.1002-beta (201903.1002b0)"
    assert expected in commits[1]


def test_grep(runner):
    _add_project_files("README.md")

    result = runner.invoke(cli, ['grep', r"vYYYY0M.BUILD[-RELEASE]", "README.md"])
    assert result.exit_code == 0
    assert "Found 1 match for pattern" in result.output

    search_re = r"^\s+2:\s+Hello World v201701\.1002-alpha !"
    assert re.search(search_re, result.output, flags=re.MULTILINE)

    result = runner.invoke(cli, ['grep', r"\[aka. YYYY0M.BLD[PYTAGNUM] \!\]", "README.md"])
    assert result.exit_code == 0
    assert "Found 1 match for pattern" in result.output

    search_re = r"^\s+3:\s+\[aka\. 201701\.1002a0 \!\]"
    assert re.search(search_re, result.output, flags=re.MULTILINE)


SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE = r"""
[pycalver]
current_version = "v201701.1002-alpha"
version_pattern = "{pycalver}"

[pycalver:file_patterns]
setup.cfg =
    current_version = "{version}"
README.md =
    Hello World {version} !
README.* =
    [aka. {pep440_version} !]
"""


def test_multimatch_file_patterns(runner):
    _add_project_files("README.md")
    with pl.Path("setup.cfg").open(mode="w", encoding="utf-8") as fobj:
        fobj.write(SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE)

    result = runner.invoke(cli, ['bump', '--release', 'beta'])
    assert result.exit_code == 0

    with pl.Path("README.md").open(mode="r", encoding="utf-8") as fobj:
        readme_text = fobj.read()

    assert "Hello World v202010.1003-beta !" in readme_text
    assert "[aka. 202010.1003b0 !]" in readme_text


def _kwargs(year, month, minor=False):
    return {'date': dt.date(year, month, 1), 'minor': minor}


ROLLOVER_TEST_CASES = [
    # v1 cases
    ["{year}.{month}.{MINOR}", "2020.10.3", "2020.10.4", _kwargs(2020, 10, True)],
    ["{year}.{month}.{MINOR}", "2020.10.3", None, _kwargs(2020, 10, False)],
    ["{year}.{month}.{MINOR}", "2020.10.3", "2020.11.4", _kwargs(2020, 11, True)],
    ["{year}.{month}.{MINOR}", "2020.10.3", "2020.11.3", _kwargs(2020, 11, False)],
    # v2 cases
    ["YYYY.MM.MINOR"  , "2020.10.3", "2020.10.4", _kwargs(2020, 10, True)],
    ["YYYY.MM.MINOR"  , "2020.10.3", None, _kwargs(2020, 10, False)],
    ["YYYY.MM.MINOR"  , "2020.10.3", "2020.11.0", _kwargs(2020, 11, True)],
    ["YYYY.MM.MINOR"  , "2020.10.3", "2020.11.0", _kwargs(2020, 11, False)],
    ["YYYY.MM[.MINOR]", "2020.10.3", "2020.10.4", _kwargs(2020, 10, True)],
    ["YYYY.MM[.MINOR]", "2020.10.3", "2020.11", _kwargs(2020, 11, False)],
    ["YYYY.MM.MINOR"  , "2020.10.3", "2021.10.0", _kwargs(2021, 10, False)],
    # incr0/incr1 part
    ["YYYY.MM.INC0", "2020.10.3", "2020.10.4", _kwargs(2020, 10)],
    ["YYYY.MM.INC0", "2020.10.3", "2020.11.0", _kwargs(2020, 11)],
    ["YYYY.MM.INC0", "2020.10.3", "2021.10.0", _kwargs(2021, 10)],
    ["YYYY.MM.INC1", "2020.10.3", "2020.10.4", _kwargs(2020, 10)],
    ["YYYY.MM.INC1", "2020.10.3", "2020.11.1", _kwargs(2020, 11)],
    ["YYYY.MM.INC1", "2020.10.3", "2021.10.1", _kwargs(2021, 10)],
]


@pytest.mark.parametrize("version_pattern, old_version, expected, kwargs", ROLLOVER_TEST_CASES)
def test_rollover(version_pattern, old_version, expected, kwargs):
    new_version = incr_dispatch(old_version, raw_pattern=version_pattern, **kwargs)
    if new_version is None:
        assert expected is None
    else:
        assert new_version == expected
