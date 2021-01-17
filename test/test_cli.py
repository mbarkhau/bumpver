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

from bumpver import cli
from bumpver import config
from bumpver import v2patterns

# pylint:disable=redefined-outer-name ; pytest fixtures
# pylint:disable=protected-access ; allowed for test code
# pylint:disable=unused-argument ; allowed for test code
# pylint:disable=too-many-lines ; allowed for test code


README_TEXT_FIXTURE = """
        Hello World v2017.1002-alpha !
        [aka. 2017.1002a0 !]
        Hello World v201707.1002-alpha !
        [aka. 201707.1002a0 !]
"""


SETUP_CFG_FIXTURE = """
[metadata]
license_file = LICENSE

[bdist_wheel]
universal = 1
"""

CALVER_TOML_FIXTURE = """
"""

PYPROJECT_TOML_FIXTURE = """
[build-system]
requires = ["setuptools", "wheel"]
"""

ENV = {
    'GIT_AUTHOR_NAME'    : "bumpver_tester",
    'GIT_COMMITTER_NAME' : "bumpver_tester",
    'GIT_AUTHOR_EMAIL'   : "bumpver_tester@nowhere.com",
    'GIT_COMMITTER_EMAIL': "bumpver_tester@nowhere.com",
    'HGUSER'             : "bumpver_tester",
    'PATH'               : os.environ['PATH'],
}


def shell(*cmd):
    return sp.check_output(cmd, env=ENV)


ECHO_CAPLOG = os.getenv('ECHO_CAPLOG') == "1"


def _debug_records(caplog):
    if ECHO_CAPLOG:
        print()
        for record in caplog.records:
            print(record)


@pytest.fixture
def runner(tmpdir):
    runner   = CliRunner(env=ENV)
    orig_cwd = os.getcwd()

    _debug = 0
    if _debug:
        tmpdir = pl.Path("..") / "tmp_test_bumpver_project"
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
    result = runner.invoke(cli.cli, ['--help', "-vv"])
    assert result.exit_code == 0
    assert "update " in result.output
    assert "test " in result.output
    assert "init " in result.output
    assert "show " in result.output


def test_version(runner):
    result = runner.invoke(cli.cli, ['--version', "-vv"])
    assert result.exit_code == 0
    assert " version 20" in result.output
    pattern = v2patterns.compile_pattern("YYYY.BUILD[-TAG]")
    match   = pattern.regexp.search(result.output)
    assert match


def test_show_env(runner):
    _add_project_files("README.md", "setup.cfg")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    result = runner.invoke(cli.cli, ['show', "-e"])
    assert result.exit_code == 0
    assert "TAG=alpha" in result.output


def test_incr_default(runner):
    old_version = "v201709.1004-alpha"

    cmd    = ['test', "-vv", "--pin-date", "--tag", "beta", old_version, "{pycalver}"]
    result = runner.invoke(cli.cli, cmd)
    assert result.exit_code == 0
    assert "Version: v201709.1005-beta\n" in result.output

    old_version = "v2017.1004-alpha"

    cmd    = ['test', "-vv", "--pin-date", "--tag", "beta", old_version, "v{year}{build}{release}"]
    result = runner.invoke(cli.cli, cmd)
    assert result.exit_code == 0
    assert "Version: v2017.1005-beta\n" in result.output

    cmd    = ['test', "-vv", "--pin-date", "--tag", "beta", old_version, "vYYYY.BUILD[-TAG]"]
    result = runner.invoke(cli.cli, cmd)
    assert result.exit_code == 0
    assert "Version: v2017.1005-beta\n" in result.output


def test_incr_pin_date(runner):
    old_version = "v2017.1999-alpha"
    pattern     = "vYYYY.BUILD[-TAG]"
    result      = runner.invoke(cli.cli, ['test', "-vv", "--pin-date", old_version, pattern])
    assert result.exit_code == 0
    assert "Version: v2017.22000-alpha\n" in result.output


def test_incr_semver(runner):
    semver_patterns = [
        "{semver}",
        "{MAJOR}.{MINOR}.{PATCH}",
        "MAJOR.MINOR.PATCH",
    ]

    for semver_pattern in semver_patterns:
        old_version = "0.1.0"
        new_version = "0.1.1"

        result = runner.invoke(cli.cli, ['test', "-vv", "--patch", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output

        old_version = "0.1.1"
        new_version = "0.2.0"

        result = runner.invoke(cli.cli, ['test', "-vv", "--minor", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output

        old_version = "0.1.1"
        new_version = "1.0.0"

        result = runner.invoke(cli.cli, ['test', "-vv", "--major", old_version, semver_pattern])
        assert result.exit_code == 0
        assert f"Version: {new_version}\n" in result.output


def test_incr_semver_invalid(runner, caplog):
    pattern = "vYYYY.BUILD[-TAG]"
    result  = runner.invoke(cli.cli, ['test', "-vv", "0.1.1", pattern, "--patch"])
    assert result.exit_code == 1
    assert len(caplog.records) > 0
    log_msg = caplog.records[0].message
    assert "--patch is not applicable to pattern" in log_msg
    assert "to pattern 'vYYYY.BUILD[-TAG]'" in log_msg


def test_incr_to_beta(runner):
    pattern     = "vYYYY.BUILD[-TAG]"
    old_version = "v2017.1999-alpha"
    new_version = dt.datetime.utcnow().strftime("v%Y.22000-beta")

    result = runner.invoke(cli.cli, ['test', "-vv", old_version, pattern, "--tag", "beta"])
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


def test_incr_to_final(runner, caplog):
    pattern     = "vYYYY.BUILD[-TAG]"
    old_version = "v2017.1999-alpha"
    new_version = dt.datetime.utcnow().strftime("v%Y.22000")

    result = runner.invoke(cli.cli, ['test', "-vv", old_version, pattern, "--tag", "final"])
    _debug_records(caplog)
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


SEMVER = "MAJOR.MINOR.PATCH[PYTAGNUM]"


def test_incr_tag(runner):
    old_version = "0.1.0"
    new_version = "0.1.1b0"

    result = runner.invoke(
        cli.cli, ['test', "-vv", old_version, SEMVER, "--patch", "--tag", "beta"]
    )
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


def test_incr_tag_num(runner):
    old_version = "0.1.0b0"
    new_version = "0.1.0b1"

    result = runner.invoke(cli.cli, ['test', "-vv", old_version, SEMVER, "--tag-num"])
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


def test_incr_invalid(runner):
    pattern     = "vYYYY.BUILD[-TAG]"
    old_version = "v2017.1999-alpha"

    result = runner.invoke(cli.cli, ['test', "-vv", old_version, pattern, "--tag", "alfa"])
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
            fobj.write(CALVER_TOML_FIXTURE)

    if "pyproject.toml" in files:
        with pl.Path("pyproject.toml").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(PYPROJECT_TOML_FIXTURE)

    if "bumpver.toml" in files:
        with pl.Path("bumpver.toml").open(mode="wt", encoding="utf-8") as fobj:
            fobj.write(CALVER_TOML_FIXTURE)


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
    result = runner.invoke(cli.cli, ['show', "-vv"])
    assert result.exit_code == 1
    expected_msg = "Could not parse configuration. Perhaps try 'bumpver init'."
    _debug_records(caplog)
    assert any(expected_msg in r.message for r in caplog.records)


def test_novcs_nocfg_init(runner, caplog):
    _add_project_files("README.md")
    # dry mode test
    result = runner.invoke(cli.cli, ['init', "-vv", "--dry"])
    assert result.exit_code == 0
    assert not os.path.exists("bumpver.toml")

    # non dry mode
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    assert os.path.exists("bumpver.toml")
    with pl.Path("bumpver.toml").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_BUMPVER_TOML_BASE_TMPL.format(
        initial_version=config._initial_version()
    )
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(cli.cli, ['show', "-vv"])
    _debug_records(caplog)
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 1

    # check logging
    assert len(caplog.records) == 1
    log = caplog.records[0]
    assert log.levelname == 'ERROR'
    assert "Configuration already initialized" in log.message


def test_novcs_setupcfg_init(runner):
    _add_project_files("README.md", "setup.cfg")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_CONFIGPARSER_BASE_TMPL.format(
        initial_version=config._initial_version()
    )
    assert base_str                                  in cfg_content
    assert config.DEFAULT_CONFIGPARSER_README_MD_STR in cfg_content

    result = runner.invoke(cli.cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_novcs_multi_cfg(runner):
    _add_project_files("README.md", "setup.cfg")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    # NOTE (mb 2020-11-16): Even though a pyproject.toml exists, it shouldn't
    #   be used because the setup.cfg has the [bumpver] config section and
    #   should have higher priorty.
    with pl.Path("pyproject.toml").open(mode="wt", encoding="utf-8") as fobj:
        fobj.write("")

    result = runner.invoke(cli.cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_novcs_pyproject_init(runner, caplog):
    _add_project_files("README.md", "pyproject.toml")
    result = runner.invoke(cli.cli, ['init', "-vv"])
    _debug_records(caplog)
    assert result.exit_code == 0

    with pl.Path("pyproject.toml").open(mode="r", encoding="utf-8") as fobj:
        cfg_content = fobj.read()

    base_str = config.DEFAULT_PYPROJECT_TOML_BASE_TMPL.format(
        initial_version=config._initial_version()
    )
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(cli.cli, ['show'])
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


_today = dt.datetime.utcnow().date()


DEFAULT_VERSION_PATTERNS = [
    ('"vYYYY0M.BUILD[-TAG]"'    , _today.strftime("v%Y%m.1001-alpha"), _today.strftime("%Y%m.1001a0")),
    ('"vYYYY.BUILD[-TAG]"'      , _today.strftime("v%Y.1001-alpha"), _today.strftime("%Y.1001a0")),
    ('"{pycalver}"'             , _today.strftime("v%Y%m.1001-alpha"), _today.strftime("%Y%m.1001a0")),
    ('"v{year}{build}{release}"', _today.strftime("v%Y.1001-alpha"), _today.strftime("%Y.1001a0")),
]


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_git_init(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    result = runner.invoke(cli.cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {cur_version}\n" in result.output


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_hg_init(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    result = runner.invoke(cli.cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {cur_version}\n" in result.output


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_v1_git_tag_eval(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("git")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    tag_version = cur_version.replace(".1001-alpha", ".1123-beta")
    assert tag_version != cur_version

    shell("git", "tag", "--annotate", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(cli.cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_hg_tag_eval(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("hg")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    tag_version        = cur_version.replace(".1001-alpha", ".1123-beta")
    tag_version_pep440 = tag_version[1:].split(".")[0] + ".1123b0"

    shell("hg", "tag", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(cli.cli, ['show', "-vv"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output
    assert f"PEP440         : {tag_version_pep440}\n" in result.output


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_novcs_bump(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    with pl.Path("README.md").open(mode="r") as fobj:
        content = fobj.read()

    result = runner.invoke(cli.cli, ['update', "-vv"])
    assert result.exit_code == 0

    calver = cur_version.split(".")[0]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content
        assert calver[1:] + ".1002a0 !]\n" in content

    result = runner.invoke(cli.cli, ['update', "-vv", "--tag", "beta"])
    assert result.exit_code == 0

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1003-beta !\n" in content
        assert calver[1:] + ".1003b0 !]\n" in content


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_git_bump(runner, caplog, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    shell("git", "add", "bumpver.toml")
    shell("git", "commit", "-m", "initial commit")

    result = runner.invoke(cli.cli, ['update', "-vv"])
    _debug_records(caplog)
    assert result.exit_code == 0

    calver = cur_version.split(".")[0]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_hg_bump(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val(
        "bumpver.toml",
        version_pattern=version_pattern,
        current_version='"' + cur_version + '"',
    )

    shell("hg", "add", "bumpver.toml")
    shell("hg", "commit", "-m", "initial commit")

    result = runner.invoke(cli.cli, ['update', "-vv"])
    assert result.exit_code == 0

    calver = cur_version.split(".")[0]

    with pl.Path("README.md").open() as fobj:
        content = fobj.read()
        assert calver + ".1002-alpha !\n" in content


def test_empty_git_bump(runner, caplog):
    shell("git", "init")
    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write("")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fobj:
        default_cfg_data = fobj.read()

    assert "[bumpver]\n" in default_cfg_data
    assert "\ncurrent_version = " in default_cfg_data
    assert "\n[bumpver:file_patterns]\n" in default_cfg_data
    assert "\nsetup.cfg =\n" in default_cfg_data

    result = runner.invoke(cli.cli, ['update'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)


def test_empty_hg_bump(runner, caplog):
    shell("hg", "init")
    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write("")

    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fobj:
        default_cfg_text = fobj.read()

    assert "[bumpver]\n" in default_cfg_text
    assert "\ncurrent_version = " in default_cfg_text
    assert "\n[bumpver:file_patterns]\n" in default_cfg_text
    assert "\nsetup.cfg =\n" in default_cfg_text

    result = runner.invoke(cli.cli, ['update'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)


SETUP_CFG_SEMVER_FIXTURE = """
[metadata]
license_file = LICENSE

[bdist_wheel]
universal = 1

[bumpver]
current_version = "0.1.0"
version_pattern = "{semver}"

[bumpver:file_patterns]
setup.cfg =
    current_version = "{version}"
"""


DEFAULT_SEMVER_PATTERNS = [
    '"{semver}"',
    '"MAJOR.MINOR.PATCH"',
]


@pytest.mark.parametrize("version_pattern", DEFAULT_SEMVER_PATTERNS)
def test_update_semver_warning(runner, caplog, version_pattern):
    _add_project_files("README.md")

    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write(SETUP_CFG_SEMVER_FIXTURE)

    _update_config_val("setup.cfg", version_pattern=version_pattern)

    _vcs_init("hg", files=["README.md", "setup.cfg"])

    result = runner.invoke(cli.cli, ['update', "-vv", "-n", "--dry"])
    assert result.exit_code == 1

    assert any("version did not change" in r.message for r in caplog.records)
    assert any("[--major/--minor/--patch] required" in r.message for r in caplog.records)

    result = runner.invoke(cli.cli, ['update', "-vv", "-n", "--dry", "--patch"])
    assert result.exit_code == 0


@pytest.mark.parametrize("version_pattern", DEFAULT_SEMVER_PATTERNS)
def test_update_semver_diff(runner, caplog, version_pattern):
    _add_project_files("README.md")

    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write(SETUP_CFG_SEMVER_FIXTURE)

    _update_config_val("setup.cfg", version_pattern=version_pattern)

    _vcs_init("hg", files=["README.md", "setup.cfg"])

    cases = [("--major", "1.0.0"), ("--minor", "0.2.0"), ("--patch", "0.1.1")]

    for flag, expected in cases:
        result = runner.invoke(cli.cli, ['update', "-vv", "-n", "--dry", flag])
        assert result.exit_code == 0
        assert len(caplog.records) == 0

        out_lines = set(result.output.splitlines())

        assert "+++ setup.cfg" in out_lines
        assert "-current_version = \"0.1.0\"" in out_lines
        assert f"+current_version = \"{expected}\"" in out_lines


def test_update_set_version(runner, caplog):
    _add_project_files("README.md", "setup.cfg")

    with pl.Path("setup.cfg").open(mode="w") as fobj:
        fobj.write(SETUP_CFG_SEMVER_FIXTURE)

    _update_config_val(
        "setup.cfg",
        version_pattern='"vYYYY.BUILD[-TAG]"',
        current_version='"v2020.1001-alpha"',
    )

    result = runner.invoke(
        cli.cli, ['update', "-vv", "-n", "--dry", "--set-version", "v2121.1234-beta"]
    )
    assert result.exit_code == 0
    assert len(caplog.records) == 0

    out_lines = set(result.output.splitlines())
    assert '-current_version = "v2020.1001-alpha"' in out_lines
    assert '+current_version = "v2121.1234-beta"' in out_lines

    result = runner.invoke(
        cli.cli, ['update', "-vv", "-n", "--dry", "--set-version", "2020.1234-invalid"]
    )
    assert result.exit_code == 1
    assert len(caplog.records) > 0

    log_msg = caplog.records[0].message
    assert "Invalid version '2020.1234-invalid' for pattern 'vYYYY.BUILD[-TAG]'" in log_msg
    log_msg = caplog.records[1].message
    assert "Invalid argument --set-version='2020.1234-invalid'" in log_msg


@pytest.mark.parametrize("version_pattern, cur_version, cur_pep440", DEFAULT_VERSION_PATTERNS)
def test_get_diff(runner, version_pattern, cur_version, cur_pep440):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    if len(cur_pep440) == 11:
        old_version = "v2017.1002-alpha"
        old_pep440  = "2017.1002a0"
    elif len(cur_pep440) == 13:
        old_version = "v201707.1002-alpha"
        old_pep440  = "201707.1002a0"
    else:
        assert False, len(cur_pep440)

    _update_config_val(
        "setup.cfg",
        version_pattern=version_pattern,
        current_version='"' + old_version + '"',
    )
    _, cfg = config.init()
    diff_str   = cli.get_diff(cfg, cur_version)
    diff_lines = set(diff_str.splitlines())

    assert f"-        Hello World {old_version} !" in diff_lines
    assert f"+        Hello World {cur_version} !" in diff_lines

    assert f"-        [aka. {old_pep440} !]" in diff_lines
    assert f"+        [aka. {cur_pep440} !]" in diff_lines

    assert f'-current_version = "{old_version}"' in diff_lines
    assert f'+current_version = "{cur_version}"' in diff_lines


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
    result = runner.invoke(cli.cli, cmd)
    assert result.exit_code == 0
    assert "New Version: " + expected in result.output


def test_hg_commit_message(runner, caplog):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    commit_message = """
    "bump from {old_version} ({old_version_pep440}) to {new_version} ({new_version_pep440})"
    """
    _update_config_val(
        "setup.cfg",
        current_version='"v2019.1001-alpha"',
        version_pattern="vYYYY.BUILD[-TAG]",
        commit_message=commit_message.strip(),
    )

    _vcs_init("hg", ["README.md", "setup.cfg"])
    assert len(caplog.records) > 0

    result = runner.invoke(cli.cli, ['update', "-vv", "--pin-date", "--tag", "beta"])
    assert result.exit_code == 0

    tags = shell("hg", "tags").decode("utf-8")
    assert "v2019.1002-beta" in tags

    commits = shell(*shlex.split("hg log -l 2")).decode("utf-8").split("\n\n")

    expected = "bump from v2019.1001-alpha (2019.1001a0) to v2019.1002-beta (2019.1002b0)"
    summary  = commits[1].split("summary:")[-1]
    assert expected in summary


def test_git_commit_message(runner, caplog):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    commit_message = """
    "bump: {old_version} ({old_version_pep440}) -> {new_version} ({new_version_pep440})"
    """
    _update_config_val(
        "setup.cfg",
        current_version='"v2019.1001-alpha"',
        version_pattern="vYYYY.BUILD[-TAG]",
        commit_message=commit_message.strip(),
    )

    _vcs_init("git", ["README.md", "setup.cfg"])
    assert len(caplog.records) > 0

    result = runner.invoke(cli.cli, ['update', "-vv", "--pin-date", "--tag", "beta"])
    assert result.exit_code == 0

    tags = shell("git", "tag", "--list").decode("utf-8")
    assert "v2019.1002-beta" in tags

    commits = shell(*shlex.split("git log -l 2")).decode("utf-8").split("\n\n")

    expected = "bump: v2019.1001-alpha (2019.1001a0) -> v2019.1002-beta (2019.1002b0)"
    assert expected in commits[1]


def test_grep(runner):
    _add_project_files("README.md")

    search_re = r"^\s+2:\s+Hello World v2017\.1002-alpha !"

    cmd1    = r'grep "vYYYY.BUILD[-TAG]" README.md'
    result1 = runner.invoke(cli.cli, shlex.split(cmd1))
    assert result1.exit_code == 0
    assert re.search(search_re, result1.output, flags=re.MULTILINE)

    cmd2    = r'grep --version-pattern "vYYYY.BUILD[-TAG]" "{version}" README.md'
    result2 = runner.invoke(cli.cli, shlex.split(cmd2))
    assert result2.exit_code == 0
    assert re.search(search_re, result2.output, flags=re.MULTILINE)

    assert result1.output == result2.output

    search_re = r"^\s+3:\s+\[aka\. 2017\.1002a0 \!\]"

    cmd3    = r'grep "\[aka. YYYY.BLD[PYTAGNUM] \!\]"  README.md'
    result3 = runner.invoke(cli.cli, shlex.split(cmd3))
    assert result3.exit_code == 0
    assert re.search(search_re, result3.output, flags=re.MULTILINE)

    cmd4    = r'grep --version-pattern "vYYYY.BUILD[-TAG]" "\[aka. {pep440_version} \!\]" README.md'
    result4 = runner.invoke(cli.cli, shlex.split(cmd4))
    assert result4.exit_code == 0
    assert re.search(search_re, result4.output, flags=re.MULTILINE)

    assert result3.output == result4.output


SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE_V1 = r"""
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


SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE_V2 = r"""
[bumpver]
current_version = "v201701.1002-alpha"
version_pattern = "vYYYY0M.BUILD[-TAG][NUM]"

[bumpver:file_patterns]
setup.cfg =
    current_version = "{version}"
README.md =
    Hello World {version} !
README.* =
    \[aka. {pep440_version} !\]
"""


@pytest.mark.parametrize(
    "config_text",
    [SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE_V1, SETUP_CFG_MULTIMATCH_FILE_PATTERNS_FIXTURE_V2],
)
def test_multimatch_file_patterns(config_text, runner):
    _add_project_files("README.md")
    with pl.Path("setup.cfg").open(mode="w", encoding="utf-8") as fobj:
        fobj.write(config_text)

    with pl.Path("README.md").open(mode="r", encoding="utf-8") as fobj:
        content = fobj.read()

    assert content.count("Hello World v201707.1002-alpha !") == 1
    assert content.count("Hello World v202011.1003-beta !") == 0
    assert content.count("[aka. 201707.1002a0 !]") == 1
    assert content.count("[aka. 202011.1003b0 !]") == 0

    result = runner.invoke(cli.cli, ['update', '--tag', 'beta', '--date', "2020-11-22"])
    assert result.exit_code == 0

    with pl.Path("README.md").open(mode="r", encoding="utf-8") as fobj:
        content = fobj.read()

    assert content.count("Hello World v201707.1002-alpha !") == 0
    assert content.count("Hello World v202011.1003-beta !") == 1
    assert content.count("[aka. 201707.1002a0 !]") == 0
    assert content.count("[aka. 202011.1003b0 !]") == 1


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
    new_version = cli.incr_dispatch(old_version, raw_pattern=version_pattern, **kwargs)
    if new_version is None:
        assert expected is None
    else:
        assert new_version == expected


def test_get_latest_vcs_version_tag(runner):
    result = runner.invoke(cli.cli, ['init', "-vv"])
    assert result.exit_code == 0

    _update_config_val("bumpver.toml", push="false")
    _update_config_val("bumpver.toml", current_version='"0.1.8"')
    _update_config_val("bumpver.toml", version_pattern='"MAJOR.MINOR.PATCH"')

    _vcs_init("git", files=["bumpver.toml"])

    result = runner.invoke(cli.cli, ['update', "--patch"])
    assert result.exit_code == 0

    _, cfg = config.init()
    latest_version = cli.get_latest_vcs_version_tag(cfg, fetch=False)
    assert latest_version == "0.1.9"

    result = runner.invoke(cli.cli, ['update', "--patch"])
    assert result.exit_code == 0

    _, cfg = config.init()
    latest_version = cli.get_latest_vcs_version_tag(cfg, fetch=False)
    assert latest_version == "0.1.10"
