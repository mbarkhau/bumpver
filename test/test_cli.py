import os
import time
import shutil
import pathlib2 as pl
import subprocess as sp

import pytest

from click.testing import CliRunner

import pycalver.config as config
import pycalver.patterns as patterns
import pycalver.__main__ as pycalver


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
}


def sh(*cmd):
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
    result = runner.invoke(pycalver.cli, ['--help', "--verbose"])
    assert result.exit_code == 0
    assert "PyCalVer" in result.output
    assert "bump " in result.output
    assert "test " in result.output
    assert "init " in result.output
    assert "show " in result.output


def test_version(runner):
    result = runner.invoke(pycalver.cli, ['--version', "--verbose"])
    assert result.exit_code == 0
    assert " version v20" in result.output
    match = patterns.PYCALVER_RE.search(result.output)
    assert match


def test_incr_default(runner):
    old_version     = "v201701.0999-alpha"
    initial_version = config._initial_version()

    result = runner.invoke(pycalver.cli, ['test', "--verbose", old_version])
    assert result.exit_code == 0
    new_version = initial_version.replace(".0001-alpha", ".11000-alpha")
    assert f"Version: {new_version}\n" in result.output


def test_incr_semver(runner):
    semver_pattern = "{MAJOR}.{MINOR}.{PATCH}"
    old_version    = "0.1.0"
    new_version    = "0.1.1"

    result = runner.invoke(pycalver.cli, ['test', "--verbose", "--patch", old_version, "{semver}"])
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output

    result = runner.invoke(
        pycalver.cli, ['test', "--verbose", "--patch", old_version, semver_pattern]
    )
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output

    old_version = "0.1.1"
    new_version = "0.2.0"

    result = runner.invoke(
        pycalver.cli, ['test', "--verbose", "--minor", old_version, semver_pattern]
    )
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output

    old_version = "0.1.1"
    new_version = "1.0.0"

    result = runner.invoke(
        pycalver.cli, ['test', "--verbose", "--major", old_version, semver_pattern]
    )
    assert result.exit_code == 0
    assert f"Version: {new_version}\n" in result.output


def test_incr_semver_invalid(runner, caplog):
    result = runner.invoke(pycalver.cli, ['test', "--verbose", "--patch", "0.1.1"])
    assert result.exit_code == 1
    assert len(caplog.records) > 0
    log_record = caplog.records[0]
    assert "Invalid version string" in log_record.message
    assert "for pattern '{pycalver}'" in log_record.message


def test_incr_to_beta(runner):
    old_version     = "v201701.0999-alpha"
    initial_version = config._initial_version()

    result = runner.invoke(pycalver.cli, ['test', old_version, "--verbose", "--release", "beta"])
    assert result.exit_code == 0
    new_version = initial_version.replace(".0001-alpha", ".11000-beta")
    assert f"Version: {new_version}\n" in result.output


def test_incr_to_final(runner):
    old_version     = "v201701.0999-alpha"
    initial_version = config._initial_version()

    result = runner.invoke(pycalver.cli, ['test', old_version, "--verbose", "--release", "final"])
    assert result.exit_code == 0
    new_version = initial_version.replace(".0001-alpha", ".11000")
    assert f"Version: {new_version}\n" in result.output


def test_incr_invalid(runner):
    old_version = "v201701.0999-alpha"

    result = runner.invoke(pycalver.cli, ['test', old_version, "--verbose", "--release", "alfa"])
    assert result.exit_code == 1


def _add_project_files(*files):
    if "README.md" in files:
        with pl.Path("README.md").open(mode="wt", encoding="utf-8") as fh:
            fh.write(
                """
                Hello World v201701.0002-alpha !
                aka. 201701.2a0 !
            """
            )

    if "setup.cfg" in files:
        with pl.Path("setup.cfg").open(mode="wt", encoding="utf-8") as fh:
            fh.write(SETUP_CFG_FIXTURE)

    if "pycalver.toml" in files:
        with pl.Path("pycalver.toml").open(mode="wt", encoding="utf-8") as fh:
            fh.write(PYCALVER_TOML_FIXTURE)

    if "pyproject.toml" in files:
        with pl.Path("pyproject.toml").open(mode="wt", encoding="utf-8") as fh:
            fh.write(PYPROJECT_TOML_FIXTURE)


def test_nocfg(runner, caplog):
    _add_project_files("README.md")
    result = runner.invoke(pycalver.cli, ['show', "--verbose"])
    assert result.exit_code == 1
    assert any(
        bool("Could not parse configuration. Perhaps try 'pycalver init'." in r.message)
        for r in caplog.records
    )


def test_novcs_nocfg_init(runner, caplog, capsys):
    _add_project_files("README.md")
    # dry mode test
    result = runner.invoke(pycalver.cli, ['init', "--verbose", "--dry"])
    assert result.exit_code == 0
    assert not os.path.exists("pycalver.toml")

    # check logging
    assert len(caplog.records) == 1
    log = caplog.records[0]
    assert log.levelname == 'WARNING'
    assert "File not found" in log.message

    # print("moep")
    # captured = capsys.readouterr()
    # assert not captured.err
    # assert "Would have written to pycalver.toml:" in captured.out

    # non dry mode
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    # check logging
    assert len(caplog.records) == 2
    log = caplog.records[1]
    assert log.levelname == 'WARNING'
    assert "File not found" in log.message

    assert os.path.exists("pycalver.toml")
    with pl.Path("pycalver.toml").open(mode="r", encoding="utf-8") as fh:
        cfg_content = fh.read()

    base_str = config.DEFAULT_TOML_BASE_TMPL.format(initial_version=config._initial_version())
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(pycalver.cli, ['show', "--verbose"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 1

    # check logging
    assert len(caplog.records) == 3
    log = caplog.records[2]
    assert log.levelname == 'ERROR'
    assert "Configuration already initialized" in log.message


def test_novcs_setupcfg_init(runner):
    _add_project_files("README.md", "setup.cfg")
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r", encoding="utf-8") as fh:
        cfg_content = fh.read()

    base_str = config.DEFAULT_CONFIGPARSER_BASE_TMPL.format(
        initial_version=config._initial_version()
    )
    assert base_str                                  in cfg_content
    assert config.DEFAULT_CONFIGPARSER_README_MD_STR in cfg_content

    result = runner.invoke(pycalver.cli, ['show', "--verbose"])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_novcs_pyproject_init(runner):
    _add_project_files("README.md", "pyproject.toml")
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    with pl.Path("pyproject.toml").open(mode="r", encoding="utf-8") as fh:
        cfg_content = fh.read()

    base_str = config.DEFAULT_TOML_BASE_TMPL.format(initial_version=config._initial_version())
    assert base_str                          in cfg_content
    assert config.DEFAULT_TOML_README_MD_STR in cfg_content

    result = runner.invoke(pycalver.cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def _vcs_init(vcs):
    assert vcs in ("git", "hg")
    assert not pl.Path(f".{vcs}").exists()
    sh(f"{vcs}", "init")
    assert pl.Path(f".{vcs}").is_dir()

    sh(f"{vcs}", "add", "README.md")
    sh(f"{vcs}", "commit", "-m", "initial commit")


def test_git_init(runner):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    result = runner.invoke(pycalver.cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_hg_init(runner):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    result = runner.invoke(pycalver.cli, ['show'])
    assert result.exit_code == 0
    assert f"Current Version: {config._initial_version()}\n" in result.output
    assert f"PEP440         : {config._initial_version_pep440()}\n" in result.output


def test_git_tag_eval(runner):
    _add_project_files("README.md")
    _vcs_init("git")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0
    initial_version    = config._initial_version()
    tag_version        = initial_version.replace(".0001-alpha", ".0123-beta")
    tag_version_pep440 = tag_version[1:7] + ".123b0"

    sh("git", "tag", "--annotate", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(pycalver.cli, ['show', "--verbose"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output
    assert f"PEP440         : {tag_version_pep440}\n" in result.output


def test_hg_tag_eval(runner):
    _add_project_files("README.md")
    _vcs_init("hg")

    # This will set a version that is older than the version tag
    # we set in the vcs, which should take precedence.
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0
    initial_version    = config._initial_version()
    tag_version        = initial_version.replace(".0001-alpha", ".0123-beta")
    tag_version_pep440 = tag_version[1:7] + ".123b0"

    sh("hg", "tag", tag_version, "--message", f"bump version to {tag_version}")

    result = runner.invoke(pycalver.cli, ['show', "--verbose"])
    assert result.exit_code == 0
    assert f"Current Version: {tag_version}\n" in result.output
    assert f"PEP440         : {tag_version_pep440}\n" in result.output


def test_novcs_bump(runner):
    _add_project_files("README.md")

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    result = runner.invoke(pycalver.cli, ['bump', "--verbose"])
    assert result.exit_code == 0

    calver = config._initial_version()[:7]

    with pl.Path("README.md").open() as fh:
        content = fh.read()
        assert calver + ".0002-alpha !\n" in content
        assert calver[1:] + ".2a0 !\n" in content

    result = runner.invoke(pycalver.cli, ['bump', "--verbose", "--release", "beta"])
    assert result.exit_code == 0

    with pl.Path("README.md").open() as fh:
        content = fh.read()
        assert calver + ".0003-beta !\n" in content
        assert calver[1:] + ".3b0 !\n" in content


def test_git_bump(runner):
    _add_project_files("README.md")
    _vcs_init("git")

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    sh("git", "add", "pycalver.toml")
    sh("git", "commit", "-m", "initial commit")

    result = runner.invoke(pycalver.cli, ['bump', "--verbose"])
    assert result.exit_code == 0

    calver = config._initial_version()[:7]

    with pl.Path("README.md").open() as fh:
        content = fh.read()
        assert calver + ".0002-alpha !\n" in content


def test_hg_bump(runner):
    _add_project_files("README.md")
    _vcs_init("hg")

    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    sh("hg", "add", "pycalver.toml")
    sh("hg", "commit", "-m", "initial commit")

    result = runner.invoke(pycalver.cli, ['bump', "--verbose"])
    assert result.exit_code == 0

    calver = config._initial_version()[:7]

    with pl.Path("README.md").open() as fh:
        content = fh.read()
        assert calver + ".0002-alpha !\n" in content


def test_empty_git_bump(runner, caplog):
    sh("git", "init")
    with pl.Path("setup.cfg").open(mode="w") as fh:
        fh.write("")
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fh:
        default_cfg_data = fh.read()

    assert "[pycalver]\n" in default_cfg_data
    assert "\ncurrent_version = " in default_cfg_data
    assert "\n[pycalver:file_patterns]\n" in default_cfg_data
    assert "\nsetup.cfg =\n" in default_cfg_data

    result = runner.invoke(pycalver.cli, ['bump'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)


def test_empty_hg_bump(runner, caplog):
    sh("hg", "init")
    with pl.Path("setup.cfg").open(mode="w") as fh:
        fh.write("")
    result = runner.invoke(pycalver.cli, ['init', "--verbose"])
    assert result.exit_code == 0

    with pl.Path("setup.cfg").open(mode="r") as fh:
        default_cfg_data = fh.read()

    assert "[pycalver]\n" in default_cfg_data
    assert "\ncurrent_version = " in default_cfg_data
    assert "\n[pycalver:file_patterns]\n" in default_cfg_data
    assert "\nsetup.cfg =\n" in default_cfg_data

    result = runner.invoke(pycalver.cli, ['bump'])

    assert any(("working directory is not clean" in r.message) for r in caplog.records)
    assert any(("setup.cfg" in r.message) for r in caplog.records)
