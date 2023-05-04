<div align="center">
<p align="center">
  <img alt="logo" src="https://raw.githubusercontent.com/mbarkhau/bumpver/master/bumpver_128.png">
</p>
</div>


# [BumpVer: Automatic Versioning][url_repo]

With the CLI command `bumpver`, you can search for and update version strings in your project files. It has a flexible pattern syntax to support many version schemes ([SemVer][url_semver_org], [CalVer][url_calver_org] or otherwise). BumpVer features:

- Configurable version patterns
- Optional Git or Mercurial integration
- Works with plaintext, so you can use it with any project.

[url_repo]: https://github.com/mbarkhau/bumpver
[url_semver_org]: https://semver.org/
[url_calver_org]: https://calver.org/


Project/Repo:

[![MIT License][img_license]][url_license]
[![Supported Python Versions][img_pyversions]][url_pyversions]
[![CalVer 2023.1121][img_version]][url_version]
[![PyPI Releases][img_pypi]][url_pypi]
[![PyPI Downloads][img_downloads]][url_downloads]

Code Quality/CI:

[![GitHub Build Status][img_github_build]][url_github_build]
[![GitLab Build Status][img_gitlab_build]][url_gitlab_build]
[![Type Checked with mypy][img_mypy]][url_mypy]
[![Code Coverage][img_codecov]][url_codecov]
[![Code Style: sjfmt][img_style]][url_style]


[img_github_build]: https://github.com/mbarkhau/pycalver/workflows/CI/badge.svg
[url_github_build]: https://github.com/mbarkhau/pycalver/actions?query=workflow%3ACI

[img_gitlab_build]: https://gitlab.com/mbarkhau/pycalver/badges/master/pipeline.svg
[url_gitlab_build]: https://gitlab.com/mbarkhau/pycalver/pipelines

[img_codecov]: https://gitlab.com/mbarkhau/pycalver/badges/master/coverage.svg
[url_codecov]: https://mbarkhau.gitlab.io/pycalver/cov

[img_license]: https://img.shields.io/badge/License-MIT-blue.svg
[url_license]: https://github.com/mbarkhau/bumpver/blob/master/LICENSE

[img_mypy]: https://img.shields.io/badge/mypy-checked-green.svg
[url_mypy]: https://mbarkhau.gitlab.io/pycalver/mypycov

[img_style]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[url_style]: https://gitlab.com/mbarkhau/straitjacket/

[img_downloads]: https://pepy.tech/badge/bumpver/month
[url_downloads]: https://pepy.tech/project/bumpver

[img_version]: https://img.shields.io/static/v1.svg?label=CalVer&message=2023.1121&color=blue
[url_version]: https://pypi.org/project/bumpver/

[img_pypi]: https://img.shields.io/badge/PyPI-wheels-green.svg
[url_pypi]: https://pypi.org/project/bumpver/#files

[img_pyversions]: https://img.shields.io/pypi/pyversions/bumpver.svg
[url_pyversions]: https://pypi.python.org/pypi/bumpver

<!--
  $ pip install -U md-toc
  $ md_toc --in-place --skip-lines 10 github README.md
-->

<!--TOC-->

- [Overview](#overview)
  - [Search and Replace](#search-and-replace)
  - [Name Change PyCalVer -> BumpVer](#name-change-pycalver---bumpver)
  - [Related Projects/Alternatives](#related-projectsalternatives)
- [Example Usage](#example-usage)
  - [Testing a `version_pattern`](#testing-a-version_pattern)
  - [Using `MAJOR`/`MINOR`/`PATCH` (SemVer Parts)](#using-majorminorpatch-semver-parts)
  - [Auto Increment Parts: `BUILD`/`INC0`/`INC1`](#auto-increment-parts-buildinc0inc1)
  - [Persistent Parts: `BUILD`/`TAG`/`PYTAG`](#persistent-parts-buildtagpytag)
  - [Searching for Patterns with `grep`](#searching-for-patterns-with-grep)
- [Reference](#reference)
  - [Command Line](#command-line)
  - [Part Overview](#part-overview)
  - [Normalization Caveats](#normalization-caveats)
  - [Pattern Examples](#pattern-examples)
  - [Week Numbering](#week-numbering)
- [Configuration](#configuration)
  - [Configuration Setup](#configuration-setup)
  - [Debugging Configuration](#debugging-configuration)
- [Bump It Up](#bump-it-up)
  - [Version State](#version-state)
  - [The Current Version](#the-current-version)
  - [Dry Mode](#dry-mode)
  - [VCS Parameters (git/mercurial)](#vcs-parameters-gitmercurial)

<!--TOC-->


## Overview

### Search and Replace

With `bumpver`, you configure a single `version_pattern` which is then used to

1. Search for version strings in your project files
2. Replace these with an updated/bumped version number.

Your configuration might look something like this:

```
[bumpver]
current_version = "1.5.2"
version_pattern = "MAJOR.MINOR.PATCH"

[bumpver:file_patterns]
setup.py
    version="{version}",$
src/mymodule/__init__.py
    ^__version__ = "{version}"$
```

Using this configuration, the output of `bumpver update --dry` might look something like this:

```diff
$ bumpver update --patch --dry
INFO    - Old Version: 1.5.2
INFO    - New Version: 1.5.3
--- setup.py
+++ setup.py
@@ -63,7 +63,7 @@
     name="mymodule",
-    version="1.5.2",
+    version="1.5.3",
     description=description,

--- src/mymodule/__init__.py
+++ src/mymodule/__init__.py
@@ -3,3 +3,3 @@

-__version__ = "1.5.2"
+__version__ = "1.5.3"
```


### Name Change PyCalVer -> BumpVer

This project was originally developed under the name PyCalVer, with the intent to support various CalVer schemes. The package has since been renamed from PyCalVer to BumpVer and the CLI command from `pycalver` to `bumpver`.

This name change is to reduce confusion that this project is only suitable for Python projects or only for CalVer versioning schemes, neither of which is the case.


### Related Projects/Alternatives

If you are looking for an alternative, BumpVer was heavily influenced by [bumpversion/bump2version][url_bump2version]. You may also wish to take a look at their list of related projects: [bump2version/RELATED.md][url_bump2version_related]

[url_bump2version]: https://github.com/c4urself/bump2version/
[url_bump2version_related]: https://github.com/c4urself/bump2version/blob/master/RELATED.md


## Example Usage

You can override the date used by `bumpver` with the  `--date=<isodate>` option. Adding this every time would be distracting, so the examples assume the following date:

```shell
$ date --iso
2020-10-15
```


### Testing a `version_pattern`

To test a `version_pattern` and how to increment it, you can use `bumpver test`:

```shell
$ bumpver test 'v2020.37' 'vYYYY.WW'
New Version: v2020.41
```

A `version_pattern` consists of three kinds of characters:

- Literal text, such as `v`, `.`, and `-`, typically used as delimiters.
- A [valid part](#parts-overview) such as `YYYY`/`WW` in the previous example.
- Square brackets `[]` to mark an optional segment.

The following example uses all three: `vYYYY.WW[-TAG]`

```
               vYYYY.WW[-TAG]
literal text   ^    ^   ^
```

```shell
$ bumpver test 'v2020.37-beta' 'vYYYY.WW[-TAG]'
New Version: v2020.41-beta
PEP440     : 2020.41b0
```

Here we see the week number changed from 37 to 41. The test command also shows the normalized version pattern according to [PEP440][pep_440_ref]. This removes the `"v"` prefix and shortens the release tag from `-beta` to `b0`.

[pep_440_ref]: https://www.python.org/dev/peps/pep-0440/

To remove the release tag, use the option `--tag=final`.

```shell
$ bumpver test 'v2020.37-beta' 'vYYYY.WW[-TAG]' --tag=final
New Version: v2020.41
PEP440     : 2020.41
```

### Using `MAJOR`/`MINOR`/`PATCH` (SemVer Parts)

A CalVer `version_pattern` may not require any flags to determine which part should be incremented, so long as the date has changed.
With SemVer you must always specify one of `--major/--minor/--patch`.

```shell
$ bumpver test '1.2.3' 'MAJOR.MINOR.PATCH[PYTAGNUM]' --major
New Version: 2.0.0

$ bumpver test '1.2.3' 'MAJOR.MINOR.PATCH[PYTAGNUM]' --minor
New Version: 1.3.0

$ bumpver test '1.2.3' 'MAJOR.MINOR.PATCH[PYTAGNUM]' --patch
New Version: 1.2.4

$ bumpver test '1.2.3' 'MAJOR.MINOR.PATCH[PYTAGNUM]' --patch --tag=beta
New Version: 1.2.4b0

$ bumpver test '1.2.4b0' 'MAJOR.MINOR.PATCH[PYTAGNUM]' --tag-num
New Version: 1.2.4b1
```

These non date based parts also make sense for a CalVer `version_pattern`, so that you can create multiple releases in the same month. It is common to include e.g. a `PATCH` part.

```shell
$ bumpver test '2020.10.0' 'YYYY.MM.PATCH' --patch
New Version: 2020.10.1
```

Without this flag, we would get an error if the date is still in October.

```shell
$ date --iso
2020-10-15

$ bumpver test '2020.10.0' 'YYYY.MM.PATCH'
ERROR   - Invalid arguments or pattern, version did not change.
ERROR   - Version did not change: '2020.10.0'. Invalid version and/or pattern 'YYYY.MM.PATCH'.
INFO    - Perhaps try: bumpver test --patch
```

Once the date is in November, the `PATCH` part will roll over back to zero. This happens whenever parts to the left change (in this case the year and month), just as it does if `MAJOR` or `MINOR` were incremented in SemVer.

```shell
$ bumpver test '2020.10.1' 'YYYY.MM.PATCH' --date 2020-11-01
New Version: 2020.11.0
```

The rollover to zero will happen even if you use the `--patch` argument, so that your first release in a month will always have a `PATCH` set to 0 instead of 1. You can make the `PATCH` part optional with `[.PATCH]` and always supply the `--patch`  flag in your build script. This will cause the part to be omitted when 0 and added when > 0.

```shell
$ bumpver test '2020.9.1' 'YYYY.MM[.PATCH]' --patch
New Version: 2020.10

$ bumpver test '2020.10' 'YYYY.MM[.PATCH]' --patch
New Version: 2020.10.1

$ bumpver test '2020.10.1' 'YYYY.MM[.PATCH]' --patch
New Version: 2020.10.2
```


With CalVer, the version is based on a calendar date, so you only have to specify such flags if you've already published a release for the current date. Without such a flag, BumpVer will show the error, that the "version did not change".

```shell
$ bumpver test 'v2020.41-beta0' 'vYYYY.WW[-TAGNUM]'
ERROR   - Invalid arguments or pattern, version did not change.
ERROR   - Invalid version 'v2020.41-beta0' and/or pattern 'vYYYY.WW[-TAGNUM]'.
```

In this case you have to change one of the parts that are not based on a calendar date.

```shell
$ bumpver test 'v2020.41-beta0' 'vYYYY.WW[-TAGNUM]' --tag-num
New Version: v2020.41-beta1
PEP440     : 2020.41b1

$ bumpver test 'v2020.41-beta0' 'vYYYY.WW[-TAGNUM]' --tag=final
New Version: v2020.41
PEP440     : 2020.41
```

If a pattern is not applicable to a version string, then you will get an error message.

```shell
$ bumpver test '2020.37' 'YYYY.MM'     # expected to fail because 37 is not valid for part MM
ERROR   - Incomplete match '2020.3' for version string '2020.37' with pattern 'YYYY.MM'/'(?P<year_y>[1-9][0-9]{3})\.(?P<month>1[0-2]|[1-9])'
ERROR   - Invalid version '2020.37' and/or pattern 'YYYY.MM'.
```

This illustrates that each pattern is internally translated to a regular expression which must match the version string. The `--verbose` flag will show a verbose form of the regular expression, which may help to debug the discrepancy between the pattern and the version.

```shell
$ bumpver test 'v2020.37' 'YYYY.WW' --verbose  # missing "v" prefix
INFO    - Using pattern YYYY.WW
INFO    - regex = re.compile(r"""
    (?P<year_y>[1-9][0-9]{3})
    \.
    (?P<week_w>5[0-2]|[1-4][0-9]|[0-9])
""", flags=re.VERBOSE)
ERROR   - Invalid version string 'v2020.37' for pattern ...
```

To fix the above, you can either remove the "v" prefix from the version or add it to the pattern.

```shell
$ bumpver test 'v2020.37' 'vYYYY.WW'   # added "v" prefix
New Version: v2020.41
PEP440     : 2020.41
```


### Auto Increment Parts: `INC0`/`INC1`/`BUILD`

These parts are incremented automatically, and do not use/require a CLI flag: `BUILD`/`INC0`/`INC1`.

```shell
$ bumpver test '2020.10.1' 'YYYY.MM.INC0'
New Version: 2020.10.2

$ bumpver test '2020.10.2' 'YYYY.MM.INC0' --date 2020-11-01
New Version: 2020.11.0
```

You can make the part optional using the `[PART]` syntax and it will be added/removed as needed.

```shell
$ bumpver test '2020.10' 'YYYY.MM[.INC0]'
New Version: 2020.10.1

$ bumpver test '2020.10.1' 'YYYY.MM[.INC0]' --date 2020-11-01
New Version: 2020.11
```

You can the `BUILD` part to [maintain lexical ordering][url_pypi_lexid]  of version numbers. This means that the expression `older < newer` will always be true, whether you are dealing with integers or strings, whether you are using software that understands how to parse version numbers or not.

```shell
$ bumpver test '2020.1001' 'YYYY.BUILD'
New Version: 2020.1002

$ bumpver test '2020.1002' 'YYYY.BUILD'
New Version: 2020.1003

$ bumpver test '2020.1999' 'YYYY.BUILD'
New Version: 2020.22000
```

[url_pypi_lexid]: https://pypi.org/project/lexid/


### Persistent Parts: `BUILD`/`TAG`/`PYTAG`

The `BUILD` and `TAG` parts will not rollover/reset. Instead they are carried forward from one version to the next.

```shell
$ bumpver test 'v2020.1051-beta' 'vYYYY.BUILD[-TAG]'
New Version: v2020.1052-beta
PEP440     : 2020.1052b0

$ bumpver test 'v2020.1051-beta' 'vYYYY.BUILD[-TAG]' --date 2021-01-01
New Version: v2021.1052-beta
PEP440     : 2021.1052b0

$ bumpver test 'v2020.1051-beta' 'vYYYY.BUILD[-TAG]' --tag=rc
New Version: v2020.1052-rc
PEP440     : 2020.1052rc0
```

To remove a release tag, mark it as final with `--tag=final`.

```shell
$ bumpver test 'v2020.1051-beta' 'vYYYY.BUILD[-TAG]' --tag=final
New Version: v2020.1052
PEP440     : 2020.1052
```


### Explicit `--set-version`

If the various automatic version incrementing methods don't work for you, you can explicitly do `--set-version=<version>`.

```diff
$ bumpver update --dry --set-version="v2020.1060"
INFO    - Old Version: v2020.1051-beta
INFO    - New Version: v2020.1060
--- setup.py
+++ setup.py
@@ -63,7 +63,7 @@
     name="mymodule",
-    version="2020.1051b0",
+    version="2020.1060",
     description=description,

--- src/mymodule/__init__.py
+++ src/mymodule/__init__.py
@@ -3,3 +3,3 @@

-__version__ = "v2020.1051-beta"
+__version__ = "v2020.1060"
```

<!--

#### Add git hash to version string

If you want to build a package straight from your git repository,
without making a release first, you can explictly add git hash to
the version number using ``GITHASH`` version part.

Let's say your ``setup.cfg`` looks like this: 

```ini
[bumpver]
...
version_pattern = "YYYY.BUILD[-TAG][GITHASH]"
...
```

Then, to update all configured files, you need to execute this command:

```shell
$ bumpver update --no-commit --no-tag --set-version="v202202.1085.8+ged2c3aaf"
```

This will modify your source tree, but won't commit or tag
anything, so you can build your packages with that version
number. Then, remember to reset local  changes after (by typing
``git reset --hard``) as standard bumpver behaviour with such
version number makes not much sense.

-->


### Searching for Patterns with `grep`

You can use `bumpver grep` to test and debug entries for your configuration.

```shell
$ bumpver grep \
	'__version__ = "YYYY.MM[-TAGNUM]"' \
	src/module/__init__.py

 3:
 4: __version__ = "2020.9-beta1"
 5:
```

When searching your project files for version strings, there are some limitations to keep in mind:

  1. A version string cannot span multiple lines.
  2. Brackets `[]` can be escaped with backslash: `\[\]`.
  3. There is no way to escape a valid part (so you cannot match the literal text `YYYY`).

Note that everything in the pattern is treated as literal text, except for a valid part (in all caps).

```
              __version__ = "YYYY.MM[-TAGNUM]"
literal text  ^^^^^^^^^^^^^^^    ^   ^       ^
```

When you write your configuration, you can avoid repeating your version pattern in every search pattern, by using these placeholders

- `{version}`
- `{pep440_version}`

Applied to the above example, you can instead write this:

```shell
$ bumpver grep \
  --version-pattern "YYYY.MM[-TAGNUM]"  \
  '__version__ = "{version}"' \
  src/module/__init__.py

 3:
 4: __version__ = "2020.9-beta1"
 5:
```

The corresponding configuration would look like this.

```ini
[bumpver]
current_version = "2020.9-beta1"
version_pattern = "YYYY.MM[-TAGNUM]"
...

[bumpver:file_patterns]
src/module/__init__.py
  __version__ = "{version}"
...
```

If you use a version pattern that is not in the PEP440 normalized form (such as the one above), you can nonetheless match version strings in your project files which *are* in the [PEP440 normalized form][url_pep_440]. To do this, you can use the placeholder `{pep440_version}` instead of the `{version}` placeholder.

```shell
$ bumpver grep --version-pattern "YYYY.MM[-TAGNUM]" 'version="{pep440_version}"' setup.py
setup.py
  65:     url="https://github.com/org/project",
  66:     version="2020.9b1",
  67:     description=description,
```

The placeholder `{version}` matches `2020.9-beta1`, while the placeholder `{pep440_version}` matches `2020.9b1` (excluding the "v" prefix, the "-" separator and with a short form release tag "b1" instead of "beta1"). These two placeholders make it possible to mostly use your preferred format for version strings, but use a PEP440 compliant/normalized version string where appropriate.

[url_pep_440]: https://www.python.org/dev/peps/pep-0440/

As a ~~neat trick~~ further illustration of how the search and replace works, you might wish to keep the year of your copyright headers up to date.

```shell
$ bumpver grep 'Copyright (c) 2018-YYYY' src/mymodule/*.py | head
src/mymodule/__init__.py
   3:
   4: # Copyright (c) 2018-2020 Vandelay Industries - All rights reserved.
   5:

src/mymodule/config.py
   3:
   4: # Copyright (c) 2018-2020 Vandelay Industries - All rights reserved.
   5:
```

The corresponding configuration for this pattern would look like this.

```ini
[bumpver:file_patterns]
...
src/mymodule/*.py
  Copyright (c) 2018-YYYY Vandelay Industries - All rights reserved.
```

Note that there must be a match for every entry in `file_patterns`. If there is no match, `bumpver` will show an error. This ensures that a pattern is not skipped when your project changes. In this case the side effect is to make sure that every file has a copyright header.

```shell
$ bumpver update --dry
ERROR   - No match for pattern 'Copyright (c) 2018-YYYY Vandelay Industries - All rights reserved.'
ERROR   -
# https://regex101.com/?flavor=python&flags=gmx&regex=Copyright%5B%20%5D%5C%28c%5C%29%0A%5B%20%5D2018%5C-%0A%28%3FP%3Cyear_y%3E%5B1-9%5D%5B0-9%5D%7B3%7D%29%0A%5B%20%5DVandelay%5B%20%5DIndustries%5B%20%5D%5C-%5B%20%5DAll%5B%20%5Drights%5B%20%5Dreserved%5C.
regex = re.compile(r"""
    Copyright[ ]\(c\)
    [ ]2018\-
    (?P<year_y>[1-9][0-9]{3})
    [ ]Vandelay[ ]Industries[ ]\-[ ]All[ ]rights[ ]reserved\.
""", flags=re.VERBOSE)
ERROR   - No patterns matched for file 'src/mymodule/utils.py'
```


## Reference

### Command Line

<!-- BEGIN bumpver --help -->

```
$ bumpver --help
Usage: bumpver [OPTIONS] COMMAND [ARGS]...

  Automatically update version strings in plaintext files.

Options:
  --version      Show the version and exit.
  --help         Show this message and exit.
  -v, --verbose  Control log level. -vv for debug level.

Commands:
  grep    Search file(s) for a version pattern.
  init    Initialize [bumpver] configuration.
  show    Show current version of your project.
  test    Increment a version number for demo purposes.
  update  Update project files with the incremented version string.
```

<!-- END bumpver --help -->

<!-- BEGIN bumpver update --help -->

```
$ bumpver update --help
Usage: bumpver update [OPTIONS]

  Update project files with the incremented version string.

Options:
  -d, --dry                       Display diff of changes, don't rewrite files.
  -f, --fetch / -n, --no-fetch    Sync tags from remote origin.
  -v, --verbose                   Control log level. -vv for debug level.
  --allow-dirty                   Commit even when working directory is has
                                  uncomitted changes. (WARNING: The commit will
                                  still be aborted if there are uncomitted to
                                  files with version strings.
  --set-version <VERSION>         Set version explicitly.
  --date <ISODATE>                Set explicit date in format YYYY-0M-0D (e.g.
                                  2021-05-13).
  --pin-date                      Leave date components unchanged.
  --pin-increments                Leave the auto-increments INC0 and INC1
  --tag-num                       Increment release tag number (rc1, rc2,
                                  rc3..).
  -t, --tag <NAME>                Override release tag of current_version. Valid
                                  options are: alpha, beta, dev, rc, post, final.
  -p, --patch                     Increment PATCH component.
  -m, --minor                     Increment MINOR component.
  --major                         Increment MAJOR component.
  -c, --commit-message <TMPL>     Set commit message template.
  --commit / --no-commit          Create a commit with all updated files.
  --tag-commit / --no-tag-commit  Tag the newly created commit.
  --push / --no-push              Push to the default remote.
  --help                          Show this message and exit.
```

<!-- END bumpver update --help -->

To help with shell script automation, you can use `bumpver show --env`.

```shell
$ bumpver show -n --env
YEAR_Y=2020
YEAR_G=
...
TAG=final
...

$ eval $(bumpver show -n --env)
$ echo $TAG
final
```


### Part Overview

> Where possible, these patterns match the conventions from [CalVer.org][url_calver_org_scheme].

[url_calver_org_scheme]: https://calver.org/#scheme

|    part    | range / example(s)         |                     info                    |
|------------|----------------------------|---------------------------------------------|
| `MAJOR`    | 0..9, 10..99, 100..        | `bumpver update --major`                    |
| `MINOR`    | 0..9, 10..99, 100..        | `bumpver update --minor`                    |
| `PATCH`    | 0..9, 10..99, 100..        | `bumpver update --patch`                    |
| `TAG`      | dev, alpha, beta, rc, post | `--tag=<tag>`                               |
| `PYTAG`    | a, b, rc, post             | `--tag=<tag>`                               |
| `NUM`      | 0, 1, 2...                 | `-r/--tag-num`                              |
| `YYYY`     | 2019, 2020...              | Full year, based on `strftime('%Y')`        |
| `YY`       | 18, 19..99, 0, 1           | Short year, based on `int(strftime('%y'))`  |
| `MM`       | 9, 10, 11, 12              | Month, based on `int(strftime('%m'))`       |
| `DD`       | 1, 2, 3..31                | Day, based on `int(strftime('%d'))`         |
| `BUILD`    | 1001, 1002 .. 1999, 22000  | build number (maintains lexical order)      |
| `INC0`     | 0, 1, 2...                 | 0-based auto incrementing number            |
| `INC1`     | 1, 2...                    | 1-based auto incrementing number            |
| `PYTAGNUM` | a0, a1, rc0, ...           | `PYTAG` + `NUM` (no white-space in between) |


The following are also available, but you should review the [Normalization Caveats](#normalization-caveats) before you decide to use them.


| part   | range / example(s)  | comment                                      |
| ------ | ------------------- | -------------------------------------------- |
| `Q`    | 1, 2, 3, 4          | Quarter                                      |
| `0Y`   | 18, 19..99, 00, 01  | Short Year `strftime('%y')`(zero-padded)     |
| `0M`   | 09, 10, 11, 12      | Month `strftime('%m')` (zero-padded)         |
| `0D`   | 01, 02, 03..31      | Day `strftime('%d')` (zero-padded)           |
| `JJJ`  | 1,2,3..366          | Day of year `int(strftime('%j'))`            |
| `00J`  | 001, 002..366       | Day of year `strftime('%j')` (zero-padded)   |
| `WW`   | 0, 1, 2..52         | Week number¹ `int(strftime('%W'))`           |
| `0W`   | 00, 01, 02..52      | Week number¹ `strftime('%W')` (zero-padded)  |
| `UU`   | 0, 1, 2..52         | Week number² `int(strftime('%U'))`           |
| `0U`   | 00, 01, 02..52      | Week number² `strftime('%U')` (zero-padded)  |
| `VV`   | 1, 2..53            | Week number¹³ `int(strftime('%V'))`          |
| `0V`   | 01, 02..53          | Week number¹³ `strftime('%V')` (zero-padded) |
| `GGGG` | 2019, 2020...       | `strftime("%G")` ISO 8601 week-based year    |
| `GG`   | 19, 20...99, 0, 1   | Short ISO 8601 week-based year               |
| `0G`   | 19, 20...99, 00, 01 | Zero-padded ISO 8601 week-based year         |

- ¹ Monday is the first day of the week.
- ² Sunday is the first day of the week.
- ³ ISO 8601 week. Week 1 contains Jan 4th.


### Normalization Caveats

Package managers and installation tools will parse your version numbers. When doing so, your version number may go through a normalization process and may not be exactly  as you specified. In the case of Python, the packaging tools (such as pip, twine, [setuptools][setuptools_ref]) follow [PEP440 normalization rules][pep_440_normalzation_ref].

According to these rules (among other things):

- Any non-numerical prefix (such as `v`) is removed
- Leading zeros in delimited parts are truncated `XX.08` -> `XX.8`
- Tags are converted to a short form (`-alpha` -> `a0`)

For example:

- Pattern: `vYY.0M.0D[-TAG]`
- Version: `v20.08.02-beta`
- PEP440 : `20.8.2b0`

I am not aware of any technical reason to use a normalized representation everywhere in your project. However, if you choose a pattern which is always in a normalized form, it will help to avoid confusion. For example, it may not be obvious at a glance, that `v20.08.02-beta` is the same as `20.8.2b0` .

A further consideration for the choice of your `version_pattern` is that it may be processed by tools that *do not* interpret it as a version number, but treat it just like any other string. It may also be confusing to your users if they a list of version numbers, sorted lexicographically by some tool (e.g. from `git tags`) and versions are not listed in order of their release:

```
$ git tag
18.6b4
18.9b0
19.10b0
19.3b0
20.8b0
20.8b1
```

If you wish to avoid this, you should use a pattern which maintains lexicographical ordering.

[setuptools_ref]: https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version

[pep_440_normalzation_ref]: https://www.python.org/dev/peps/pep-0440/#id31


### Pattern Examples

<!-- BEGIN pattern_examples -->

|             pattern             |               examples              | PEP440 | lexico. |
|---------------------------------|-------------------------------------|--------|---------|
| `MAJOR.MINOR.PATCH[PYTAGNUM]`   | `0.13.10          0.16.10rc1`       | yes    | no      |
| `MAJOR.MINOR[.PATCH[PYTAGNUM]]` | `1.11             0.3.0b5`          | yes    | no      |
| `YYYY.BUILD[PYTAGNUM]`          | `2020.1031        2020.1148a0`      | yes    | yes     |
| `YYYY.BUILD[-TAG]`              | `2021.1393-beta   2022.1279`        | no     | yes     |
| `YYYY.INC0[PYTAGNUM]`           | `2020.10          2021.12b2`        | yes    | no      |
| `YYYY0M.PATCH[-TAG]`            | `202005.12        202210.15-beta`   | no     | no¹     |
| `YYYY0M.BUILD[-TAG]`            | `202106.1071      202106.1075-beta` | no     | yes     |
| `YYYY.0M`                       | `2020.02          2022.09`          | no     | yes     |
| `YYYY.MM`                       | `2020.8           2020.10`          | yes    | no      |
| `YYYY.WW`                       | `2020.8           2021.14`          | yes    | no      |
| `YYYY.MM.PATCH[PYTAGNUM]`       | `2020.3.12b0      2021.6.19b0`      | yes    | no      |
| `YYYY.0M.PATCH[PYTAGNUM]`       | `2020.10.15b0     2022.07.7b0`      | no     | no¹     |
| `YYYY.MM.INC0`                  | `2021.6.2         2022.8.9`         | yes    | no      |
| `YYYY.MM.DD`                    | `2020.5.18        2021.8.2`         | yes    | no      |
| `YYYY.0M.0D`                    | `2020.08.24       2022.05.03`       | no     | yes     |
| `YY.0M.PATCH`                   | `21.04.2          21.11.12`         | no     | no²     |

<!-- END pattern_examples -->

- ¹ If `PATCH > 9`
- ² For the year 2100, the part `YY` will produce 0


### Week Numbering

Week numbering is a bit special, as it depends on your definition of "week":

- First day of the week is either Monday or Sunday.
- Range either from 0-52 or 1-53.
- At the beginning/end of the year, you either have partial weeks or a week that spans multiple years.

If you use `VV`/`0V`, be aware that you cannot also use `YYYY`.
Instead use `GGGG`. This is to avoid an edge case where your version
number would run backwards if it was created around New Year.


<!-- BEGIN weeknum_example -->

```sql
                   YYYY WW UU  GGGG VV
2020-12-26 (Sat):  2020 51 51  2020 52
2020-12-27 (Sun):  2020 51 52  2020 52
2020-12-28 (Mon):  2020 52 52  2020 53
2020-12-29 (Tue):  2020 52 52  2020 53
2020-12-30 (Wed):  2020 52 52  2020 53
2020-12-31 (Thu):  2020 52 52  2020 53
2021-01-01 (Fri):  2021 00 00  2020 53
2021-01-02 (Sat):  2021 00 00  2020 53
2021-01-03 (Sun):  2021 00 01  2020 53
2021-01-04 (Mon):  2021 01 01  2021 01
```

<!-- END weeknum_example -->


## Configuration

### Configuration Setup

The create an initial configuration for project with `bumpver init`.

```shell
$ pip install bumpver
...
Installing collected packages: click toml lexid bumpver
Successfully installed bumpver-2023.1121

$ cd myproject
~/myproject/

$ bumpver init --dry
Exiting because of '-d/--dry'. Would have written to bumpver.toml:

    [bumpver]
    current_version = "2020.1001a0"
    version_pattern = "YYYY.BUILD[PYTAGNUM]"
    commit_message = "bump version to {new_version}"
    commit = true
    tag = true
    push = true

    [bumpver.file_patterns]
    "README.md" = [
        "{version}",
        "{pep440_version}",
    ]
    "bumpver.toml" = [
        'current_version = "{version}"',
    ]
```

If you already have configuration file in your project (such as `setup.cfg` or `pyproject.toml`), then `bumpver init` will update that file instead.

```
~/myproject
$ bumpver init
Updated setup.cfg
```

Your `setup.cfg` may now look something like this:

```ini
[bumpver]
current_version = "2019.1001-alpha"
version_pattern = "YYYY.BUILD[-TAG]"
commit_message = "bump version to {new_version}"
commit = True
tag = True
push = True

[bumpver:file_patterns]
setup.cfg =
    current_version = "{version}"
setup.py =
    version="{pep440_version}",
README.md =
    {version}
    {pep440_version}
```


### Debugging Configuration

For the entries in `[bumpver:file_patterns]` you can expect two failure modes:

- False negative: A pattern *will not* match a version number in the associated file *which it should* match.
- False positive: A pattern *will* match something it *should not match* (less likely).

Most obviously you will see such cases when you first attempt to use `bumpver update`:

```shell
$ bumpver update --dry --no-fetch
INFO    - Old Version: 2020.1001-alpha
INFO    - New Version: 2020.1002-alpha
ERROR   - No match for pattern 'version="YYYY.BUILD[PYTAGNUM]",'
ERROR   -
# https://regex101.com/?flavor=python&flags=gmx&regex=version%3D%5C%22%0A%28%3FP%3Cyear_y%3E%5B1-9%5D%5B0-9%5D%7B3%7D%29%0A%5C.%0A%28%3FP%3Cbid%3E%5B1-9%5D%5B0-9%5D%2A%29%0A%28%3F%3A%0A%20%20%20%20%28%3FP%3Cpytag%3Epost%7Crc%7Ca%7Cb%29%0A%20%20%20%20%28%3FP%3Cnum%3E%5B0-9%5D%2B%29%0A%29%3F%0A%5C%22%2C
regex = re.compile(r"""
    version=\"
    (?P<year_y>[1-9][0-9]{3})
    \.
    (?P<bid>[1-9][0-9]*)
    (?:
        (?P<pytag>post|rc|a|b)
        (?P<num>[0-9]+)
    )?
    \",
""", flags=re.VERBOSE)
ERROR   - No patterns matched for file 'setup.py'
```

The internally used regular expression is also shown, which you can use to debug the issue, for example on [regex101.com](https://regex101.com/r/ajQDTz/2).

To debug such issues, you can simplify your pattern and see if you can find a match with `bumpver grep` .

```shell
$ bumpver grep 'YYYY.BUILD[PYTAGNUM]' setup.py
 45:    name='myproject',
 46:    version='2019.1001b0',
 47:    license='MIT',

```

Here we can see that the pattern for setup.py should be changed to used single quotes instead of doublequotes.

As with `bumpver update`, if your pattern is not found, `bumpver grep` will show an error message with the regular expression it uses, to help you debug the issue.

```shell
$ bumpver grep 'YYYY.BUILD[PYTAGNUM]' setup.py
ERROR   - Pattern not found: 'YYYY.BUILD[PYTAGNUM]'
# https://regex101.com/...
```

An example of a more complex pattern is one where you want to keep a version badge in your README up to date.

```shell
$ bumpver grep 'shields.io/badge/CalVer-YYYY.BUILD[--TAG]-blue' README.md
  61:
  62: [img_version]: https://img.shields.io/badge/CalVer-2020.1001--beta-blue
  63: [url_version]: https://pypi.org/org/package/
```


## Bump It Up


### Version State

The `current_version` is considered global state and must be stored somewhere. Typically this might be in a `VERSION` file, or some other file which is part of the repository. This creates the risk that parallel branches can have different states. If the `current_version`  were defined only by files in the local checkout, the same version might be generated on different systems for different commits.

To avoid this issue, `bumpver` treats Git/Mercurial tags as the canonical / [SSOT][url_ssot] for the most recent version and attempts to change this state in the most atomic way possible. This is why some actions of the `bumpver` command can take a few seconds, as it is synchronizing with the remote repository to get the most recent versions and to push any new version tags as soon as possible.

[url_ssot]: https://en.wikipedia.org/wiki/Single_source_of_truth


### The Current Version

The current version is either

 - Typically: The largest Git/Mercurial tag which matches the `version_pattern` from your config, sorted using [`pkg_resources.parse_version`][url_setuptools_pkg_resources].
 - Rarely: Before any tags have been created, the value of `current_version` in `bumpver.toml` / `setup.cfg` / `pyproject.toml`.

[url_setuptools_pkg_resources]: https://setuptools.readthedocs.io/en/latest/pkg_resources.html#parsing-utilities

As part of doing `bumpver update` and `bumpver show`, your local tags are updated using `git fetch --tags`/`hg pull`.

```shell
$ bumpver show -vv
2020-10-18T20:20:58.062 DEBUG   bumpver.cli       - Logging configured.
2020-10-18T20:20:58.065 DEBUG   bumpver.config    - Config Parsed: Config(
    ...
2020-10-18T20:20:58.067 DEBUG   bumpver.vcs       - vcs found: git
2020-10-18T20:20:58.067 INFO    bumpver.vcs       - fetching tags from remote (to turn off use: -n / --no-fetch)
2020-10-18T20:20:58.068 DEBUG   bumpver.vcs       - git fetch
2020-10-18T20:21:00.886 DEBUG   bumpver.vcs       - git tag --list
2020-10-18T20:21:00.890 INFO    bumpver.cli       - Latest version from git tag: 2020.1019
Current Version: 2020.1019
```

Here we see that:

- Git had a newer version than we had locally (`2020.1019` vs `2020.1018`).
- It took 2 seconds to fetch the tags from the remote repository.

The approach of fetching tags before the version is bumped/incremented, helps to reduce the risk that the newest tag is not known locally. This means that it less likely for the same version to be generated by different systems for different commits. This would result in an ambiguous version tag, which may not be the end of the world, but is better to avoid. Typically this might happen if you have a build system where multiple builds are triggered at the same time.

For a small project (with only one maintainer and no automated packaging) this is a non-issue and you can always use `-n/--no-fetch` to skip fetching the tags.


### Dry Mode

Once you have a valid configuration, you can use `bumpver update --dry` to see  the changes it would make (and leave your project files untouched).

```diff
$ bumpver update --dry --no-fetch
INFO    - Old Version: 2019.1001-beta
INFO    - New Version: 2019.1002-beta
--- README.md
+++ README.md
@@ -11,7 +11,7 @@

 [![Supported Python Versions][pyversions_img]][pyversions_ref]
-[![Version 2019.1001-beta][version_img]][version_ref]
+[![Version 2019.1002-beta][version_img]][version_ref]
 [![PyPI Releases][pypi_img]][pypi_ref]

--- src/mymodule_v1/__init__.py
+++ src/mymodule_v1/__init__.py
@@ -1,1 +1,1 @@
-__version__ = "2019.1001-beta"
+__version__ = "2019.1002-beta"

--- src/mymodule_v2/__init__.py
+++ src/mymodule_v2/__init__.py
@@ -1,1 +1,1 @@
-__version__ = "2019.1001-beta"
+__version__ = "2019.1002-beta"

--- setup.py
+++ setup.py
@@ -44,7 +44,7 @@
     name="myproject",
-    version="2019.1001b0",
+    version="2019.1002b0",
     license="MIT",
```


### VCS Parameters (git/mercurial)

The individual steps performed by `bumpver update`:

0. Check that you have no local changes that are uncommitted.
1. *Fetch* the most recent global VCS tags from origin.
2. Generate the updated version string.
3. Replace version strings in all files configured in `file_patterns`.
4. *Commit* the updated files.
5. *Tag* the new commit.
6. *Push* the new commit and tag.

The configuration for these steps can be done with the following parameters:

|    Parameter     |   Type   |               Description               |
|------------------|----------|-----------------------------------------|
| `commit_message` | string¹  | Template for commit message in step 4.  |
| `commit`         | boolean  | Create a commit with all updated files. |
| `tag`            | boolean² | Tag the newly created commit.           |
| `push`           | boolean² | Push to the default remote.             |

- ¹ Available placeholders for the `commit_message`: `{new_version}`, `{old_version}`, `{new_version_pep440}`, `{old_version_pep440}`
- ² Requires `commit = True`

An example configuration might look like this:

```ini
[bumpver]
...
commit_message = "bump version to {new_version}"
commit = True
tag = True
push = True
```

If everything looks OK, you can do `bumpver update`.

```shell
$ bumpver update --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Old Version: 2020.1005
INFO    - New Version: 2020.1006
INFO    - git commit --message 'bump version to 2020.1006'
INFO    - git tag --annotate 2020.1006 --message 2020.1006
INFO    - git push origin --follow-tags 2020.1006 HEAD
```

You can also override the config values by passing these command line flags to `bumpver update`:

|       Flag        |                 Override config                 |
|-------------------|-------------------------------------------------|
| `--commit`        | `commit = True`                                 |
| `--no-commit`     | `commit = False`, `tag = False`, `push = False` |
| `--tag-commit`    | `tag = True`                                    |
| `--no-tag-commit` | `tag = False`                                   |
| `--push`          | `push = True`                                   |
| `--no-push`       | `push = False`                                  |


### Custom Commit Message

In addition to the `commit_message` configuration, you can also override the string used as the the commit message template with the `-c/--commit-message=<TMPL>` parameter:

```shell
$ bumpver update --tag final --commit-message 'bump version {old_version} -> {new_version} [ci-publish]' --verbose
INFO    - Old Version: 2021.1005b0
INFO    - New Version: 2021.1006
INFO    - git commit --message 'bump version 2020.1005b0 -> 2021.1006 [ci-publish]'
INFO    - git tag --annotate 2020.1006 --message 2020.1006
INFO    - git push origin --follow-tags 2020.1006 HEAD
```

As this is a manual operation (rather than a long lived configuration option), you can use the placeholders `OLD` and `NEW` for convenience, instead of the more verbose `{old_version}` and `{new_version}`.

```shell
$ bumpver update -f -t final -c '[final-version] OLD -> NEW'
...
INFO    - Old Version: 1.2.0b2
INFO    - New Version: 1.2.0
INFO    - git commit --message '[final-version] 1.2.0b2 -> 1.2.0'
...
```


## Contributors

|                Name                 |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-09 | -     |
