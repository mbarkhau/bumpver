<div align="center">
<p align="center">
  <img alt="logo" src="https://gitlab.com/mbarkhau/pycalver/-/raw/master/pycalver1k2_128.png">
</p>
</div>


# [Python CalVer: Automatic Calendar Versioning][url_repo]

Python CalVer provides the CLI command `calver`. You can use it to search and update version strings in your project files. It has a flexible pattern syntax to support many version string schemes ([calver][url_calver_org], [semver][url_semver_org] or otherwise). PyCalVer features:

- Configurable version patterns
- Git, Mercurial or no VCS
- Operates only on plaintext files, so it can be used for any project, not just python projects.

[url_repo]: https://gitlab.com/mbarkhau/pycalver
[url_calver_org]: https://calver.org/
[url_semver_org]: https://semver.org/


Project/Repo:

[![MIT License][img_license]][url_license]
[![Supported Python Versions][img_pyversions]][url_pyversions]
[![CalVer v2020.1041-beta][img_version]][url_version]
[![PyPI Releases][img_pypi]][url_pypi]
[![PyPI Downloads][img_downloads]][url_downloads]

Code Quality/CI:

[![GitHub Build Status][img_github_build]][url_github_build]
[![GitLab Build Status][img_gitlab_build]][url_gitlab_build]
[![Type Checked with mypy][img_mypy]][url_mypy]
[![Code Coverage][img_codecov]][url_codecov]
[![Code Style: sjfmt][img_style]][url_style]


|                Name                 |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-09 | -     |



[img_github_build]: https://github.com/mbarkhau/pycalver/workflows/CI/badge.svg
[url_github_build]: https://github.com/mbarkhau/pycalver/actions?query=workflow%3ACI

[img_gitlab_build]: https://gitlab.com/mbarkhau/pycalver/badges/master/pipeline.svg
[url_gitlab_build]: https://gitlab.com/mbarkhau/pycalver/pipelines

[img_codecov]: https://gitlab.com/mbarkhau/pycalver/badges/master/coverage.svg
[url_codecov]: https://mbarkhau.gitlab.io/pycalver/cov

[img_license]: https://img.shields.io/badge/License-MIT-blue.svg
[url_license]: https://gitlab.com/mbarkhau/pycalver/blob/master/LICENSE

[img_mypy]: https://img.shields.io/badge/mypy-checked-green.svg
[url_mypy]: https://mbarkhau.gitlab.io/pycalver/mypycov

[img_style]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[url_style]: https://gitlab.com/mbarkhau/straitjacket/

[img_downloads]: https://pepy.tech/badge/pycalver/month
[url_downloads]: https://pepy.tech/project/pycalver

[img_version]: https://img.shields.io/static/v1.svg?label=CalVer&message=v2020.1041-beta&color=blue
[url_version]: https://pypi.org/project/pycalver/

[img_pypi]: https://img.shields.io/badge/PyPI-wheels-green.svg
[url_pypi]: https://pypi.org/project/pycalver/#files

[img_pyversions]: https://img.shields.io/pypi/pyversions/pycalver.svg
[url_pyversions]: https://pypi.python.org/pypi/pycalver


[](TOC)

- [PyCalVer: Automatic Calendar Versioning](#pycalver-automatic-calendar-versioning)
  - [Usage](#usage)
    - [Configuration](#configuration)
    - [Pattern Search and Replacement](#pattern-search-and-replacement)
    - [Week Numbering](#week-numbering)
    - [Normalization Caveats](#normalization-caveats)
    - [Legacy Patterns](#legacy-patterns)
    - [Pattern Usage](#pattern-usage)
    - [Examples](#examples)
    - [Version State](#version-state)
    - [The Current Version](#the-current-version)
    - [Bump It Up](#bump-it-up)
    - [Config Parameters](#config-parameters)
    - [CLI Reference](#cli-reference)
  - [The PyCalVer Format](#the-pycalver-format)
    - [Parsing](#parsing)
    - [Incrementing Behaviour](#incrementing-behaviour)
  - [Semantics of PyCalVer](#semantics-of-pycalver)
    - [Pitch](#pitch)
    - [blah](#blah)
    - [Intentional Breaking Changes](#intentional-breaking-changes)
    - [Costs and Benefits](#costs-and-benefits)
    - [Unintentional Breaking Changes](#unintentional-breaking-changes)
    - [Pinning is not a Panacea](#pinning-is-not-a-panacea)
    - [Zeno's 1.0 and The Eternal Beta](#zenos-10-and-the-eternal-beta)

[](TOC)


## Overview

### Search and Replace

With `calver`, you configure a single `version_pattern` which is then used to

1. Search for version strings in your project files
2. Replace these occurrences with an updated/bumped version number.

Your configuration might look something like this:

```
[calver]
current_version = "2020.9.0"
version_pattern = "YYYY.MM.PATCH"

[calver:file_patterns]
src/mymodule/__init__.py
	__version__ = "{version}"
src/mymodule/__main__.py
	@click.version_option(version="{version}")
setup.py
	version="{version}",
```

> Throughout the examples, we use the `--date` argument. Without this argument `calver` will just use the current UTC date. We use it here so that you can easily reproduce the examples.

Using this configuration, the output of `calver bump --dry` might look something like this:

```diff
$ calver bump --date 2020-10-21 --dry
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Old Version: 2020.9.0
INFO    - New Version: 2020.10.0
--- setup.py
+++ setup.py
@@ -63,7 +63,7 @@
 setuptools.setup(
     name="mymodule",
-    version="2020.9.0",
+    version="2020.10.0",
     description=description,
     long_description=long_description,

--- src/mymodule/__init__.py
+++ src/mymodule/__init__.py
@@ -3,3 +3,3 @@

-__version__ = "2020.9.0"
+__version__ = "2020.10.0"


--- src/mymodule/__main__.py
+++ src/mymodule/__main__.py
@@ -101,7 +101,7 @@

 @click.group()
-@click.version_option(version="2020.9.0")
+@click.version_option(version="2020.10.0")
 @click.help_option()
 @click.option('-v', '--verbose', count=True, help="Control log level. -vv for debug level.")
```



### Related Projects/Alternatives

If PyCalVer does not serve your purposes, you may wish to look at the [bump2version][url_bump2version] project, by which PyCalVer was heavily inspired. You may also wish to take a look at their list of related projects: [bump2version/RELATED.md][url_bump2version_related]

[url_bump2version] https://github.com/c4urself/bump2version/

[url_bump2version_related] https://github.com/c4urself/bump2version/blob/master/RELATED.md

## Example Usage

### Testing a version pattern

You can validate a pattern and how it is incremented using `calver test`.

```shell
$ calver test --date 2020-09-22 '2020.37' 'YYYY.WW'
New Version: 2020.38
PEP440     : 2020.38

$ calver test --date 2020-09-22 '2020.37' 'YYYY.MM'     # expected to fail because 37 is not valid for part MM
ERROR   - Incomplete match '2020.3' for version string '2020.37' with pattern 'YYYY.MM'/'(?P<year_y>[1-9][0-9]{3})\.(?P<month>1[0-2]|[1-9])'
ERROR   - Invalid version '2020.37' and/or pattern 'YYYY.MM'.
```

This illustrates that each pattern is internally translated to a regular expression which must match your version string. The `--verbose` flag shows a slightly more readable form.

```shell
$ calver test --date 2018-09-22 'v2018.37' 'YYYY.WW' --verbose
INFO    - Using pattern YYYY.WW
INFO    - regex = re.compile(r"""
    (?P<year_y>[1-9][0-9]{3})
    \.
    (?P<week_w>5[0-2]|[1-4][0-9]|[0-9])
""", flags=re.VERBOSE)
ERROR   - Invalid version string 'v2018.37' for pattern ...
```

In other words, you don't specify regular expressions manually, they are generated for by PyCalVer based on the parts defined in the [Parts Overview](#parts-overview).


### SemVer: `MAJOR`/`MINOR`/`PATCH`

You can do tradition SemVer without any kind of calendar component if you like.

```shell
$ calver test '1.2.3' 'MAJOR.MINOR.PATCH' --patch
New Version: 1.2.4
PEP440     : 1.2.4

$ calver test '1.2.3' 'MAJOR.MINOR.PATCH' --minor
New Version: 1.3.0
PEP440     : 1.3.0

$ calver test '1.2.3' 'MAJOR.MINOR.PATCH' --major
New Version: 2.0.0
PEP440     : 2.0.0
```

These are the same CLI flags as are accepted by the `calver bump` command.

In the context of a CalVer version, a typical use would be to include a `PATCH` part in your version pattern, so that you can create multiple releases in the same month.

```shell
$ calver test --date 2018-09-22 '2018.9.0' 'YYYY.MM.PATCH'
ERROR   - Invalid arguments or pattern, version did not change.
ERROR   - Version did not change: '2018.9.0'. Invalid version and/or pattern 'YYYY.MM.PATCH'.
INFO    - Perhaps try: calver test --patch

$ calver test --date 2018-09-22 '2018.9.0' 'YYYY.MM.PATCH' --patch
New Version: 2018.9.1
PEP440     : 2018.9.1
```

The `PATCH` part will roll over back to zero when leading parts change (in this case the year and month).

```shell
$ calver test --date 2018-10-22 '2018.9.1' 'YYYY.MM.PATCH'
New Version: 2018.10.0
PEP440     : 2018.10.0
```

This will happen even if you use the `--patch` argument, so that your first release of the month has a `PATCH` of 0 instead of 1.

```shell
$ calver test --date 2018-10-22 '2018.9.1' 'YYYY.MM.PATCH' --patch
New Version: 2018.10.0
PEP440     : 2018.10.0
```


### Auto Increment Parts: `BUILD`/`INC0`/`INC1`

The following parts are incremented automatically, and do not use/require a CLI flag: `BUILD`/`INC0`/`INC1`. This means you can just do `calver bump` without any further CLI flags and special cases, which can simplify your build scripts.

```shell
$ calver test --date 2018-09-22 '2018.9.1' 'YYYY.MM.INC0'
New Version: 2018.9.2
PEP440     : 2018.9.2

$ calver test --date 2018-10-22 '2018.9.2' 'YYYY.MM.INC0'
New Version: 2018.10.0
PEP440     : 2018.10.0

$ calver test --date 2018-10-22 '2018.9.2' 'YYYY.MM.INC1'
New Version: 2018.10.1
PEP440     : 2018.10.1
```

If it is rare for you to make multiple releases within a given period, you can make such a part optional using the `[PART]` syntax with square brackets:

```shell
$ calver test --date 2018-09-22 '2018.9' 'YYYY.MM[.INC0]'
New Version: 2018.9.1
PEP440     : 2018.9.1

$ calver test --date 2018-10-22 '2018.9.1' 'YYYY.MM[.INC0]'
New Version: 2018.10
PEP440     : 2018.10
```

If the extra `INC0` part is needed, it is added. If the date rolls over and it's no longer needed, it is omitted. Any literal text enclosed in the brackets (such as a separator) will also be added or omitted as needed.


### Persistent Parts: `BUILD`/`RELEASE`/`PYTAG`

The `BUILD` and `RELEASE` parts are not reset. Instead they are carried forward.

```shell
$ calver test --date 2018-09-22 '201809.1051-beta' 'YYYY0M.BUILD[-RELEASE]'
New Version: 201809.1052-beta
PEP440     : 201809.1052b0

$ calver test --date 2018-09-22 '201809.1051-beta' 'YYYY0M.BUILD[-RELEASE]' --release rc
New Version: 201809.1052-rc
PEP440     : 201809.1052rc0
```

To remove a release tag, mark it as final with `--release final`.

```shell
$ calver test --date 2018-09-22 '201809.1051-beta' 'YYYY0M.BUILD[-RELEASE]' --release final
New Version: 201809.1052
PEP440     : 201809.1052
```


### Searching for Patterns with `grep`

When searching for a pattern, There are some limitations to keep in mind:

  1. A version string cannot span multiple lines.
  2. There is no mechanism for escaping parts.
  3. Brackets `[]` can be escaped with backslash.

Using `calver grep`, you can search for occurrences of a version pattern in your project files.

```shell
$ calver grep '__version__ = "YYYY.MM[-RELEASENUM]"' src/module/__init__.py
src/module/__init__.py
 3:
 4: __version__ = "2020.9-beta1"
 5:
```

Note that everything in the pattern is treated as literal text, except for a valid part (in all caps).

When you write your configuration, you can avoid repeating your version pattern in every search pattern, by using these placeholders

- `{version}`
- `{pep440_version}`

Applied to the above example, you can instead use this:

```shell
$ calver grep --version-pattern "YYYY.MM[-RELEASENUM]"  '__version__ = "{version}"' src/module/__init__.py
src/module/__init__.py
 3:
 4: __version__ = "2020.9-beta1"
 5:
```

The corresponding configuration would look like this.

```ini
[calver]
current_version = "2020.9-beta1"
version_pattern = "YYYY.MM[-RELEASENUM]"
...

[calver:file_patterns]
src/module/__init__.py
  __version__ = "{version}"
...
```

If your pattern produces non PEP440 version numbers, you may wish to use the placeholder `{pep440_version}` in your search pattern and specify your `--version-pattern` separately.

```shell
$ calver grep --version-pattern "YYYY.MM[-RELEASENUM]" 'version="{pep440_version}"' setup.py
setup.py
  65:     url="https://github.com/org/project",
  66:     version="2020.9b1",
  67:     description=description,
```

The placeholder `{version}` matches `2020.9-beta1`, while the placeholder `{pep440_version}` matches `2020.9b1` (excluding the "v" prefix, the "-" separator and with a short form release tag "b1" instead of "beta1"). These two placeholders make it possible to mostly use your preferred format for version strings, but use a [PEP440][url_pep_440] compliant/normalized version string where appropriate.

[url_pep_440]: https://www.python.org/dev/peps/pep-0440/

As a further illustration of how the search and replace works, you might want use a file pattern entry to keep the year of your copyright header up to date.

```
$ calver grep 'Copyright (c) 2018-YYYY' src/mymodule/*.py | head
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
[calver:file_patterns]
...
src/mymodule/*.py
  Copyright (c) 2018-YYYY Vandelay Industries - All rights reserved.
```


## Reference

### Command Line

<!-- BEGIN calver --help -->

```
$ calver --help
Usage: calver [OPTIONS] COMMAND [ARGS]...

  Automatically update PyCalVer version strings in all project files.

Options:
  --version      Show the version and exit.
  --help         Show this message and exit.
  -v, --verbose  Control log level. -vv for debug level.

Commands:
  bump  Increment the current version string and update project files.
  grep  Search file(s) for a version pattern.
  init  Initialize [calver] configuration.
  show  Show current version of your project.
  test  Increment a version number for demo purposes.
```

<!-- END calver --help -->

<!-- BEGIN calver bump --help -->

```
$ calver bump --help
Usage: calver bump [OPTIONS]

  Increment the current version string and update project files.

Options:
  -v, --verbose                 Control log level. -vv for debug level.
  -f, --fetch / -n, --no-fetch  Sync tags from remote origin.
  -d, --dry                     Display diff of changes, don't rewrite files.
  --release <NAME>              Override release name of current_version.
                                Valid options are: alpha, beta, rc, post,
                                final.

  --allow-dirty                 Commit even when working directory is has
                                uncomitted changes. (WARNING: The commit will
                                still be aborted if there are uncomitted to
                                files with version strings.

  --major                       Increment major component.
  -m, --minor                   Increment minor component.
  -p, --patch                   Increment patch component.
  -r, --release-num             Increment release number (rc1, rc2, rc3..).
  --pin-date                    Leave date components unchanged.
  --date <ISODATE>              Set explicit date in format YYYY-0M-0D (e.g.
                                2020-10-09).

  --help                        Show this message and exit.
```

<!-- END calver bump --help -->


### Part Overview

> Where possible, these patterns match the conventions from [calver.org][url_calver_org_scheme].

[url_calver_org_scheme]: https://calver.org/#scheme

|   part  |     range / example(s)    |                  comment                   |
|---------|---------------------------|--------------------------------------------|
| `YYYY`  | 2019, 2020...             | Full year, based on `strftime('%Y')`       |
| `YY`    | 18, 19..99, 0, 1          | Short year, based on `int(strftime('%y'))` |
| `MM`    | 9, 10, 11, 12             | Month, based on `int(strftime('%m'))`      |
| `DD`    | 1, 2, 3..31               | Day, based on `int(strftime('%d'))`        |
| `MAJOR` | 0..9, 10..99, 100..       | `calver bump --major`                    |
| `MINOR` | 0..9, 10..99, 100..       | `calver bump --minor`                    |
| `PATCH` | 0..9, 10..99, 100..       | `calver bump --patch`                    |
| `TAG`   | alpha, beta, rc, post     | `--tag=<tag>`                          |
| `PYTAG` | a, b, rc, post            | `--tag=<tag>`                          |
| `NUM`   | 0, 1, 2...                | `-r/--release-num`                         |
| `BUILD` | 1001, 1002 .. 1999, 22000 | build number (maintains lexical order)     |
| `INC0`  | 0, 1, 2...                | 0-based auto incrementing number           |
| `INC1`  | 1, 2...                   | 1-based auto incrementing number           |


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

Package managers and installation tools will parse your version numbers. When doing so, your version number may go through a normalization process and may not be displayed as you specified it. In the case of Python, the packaging tools (such as pip, twine, setuptools) follow [PEP440 normalization rules][pep_440_normalzation_ref].

According to these rules (among other things):

- Any non-numerical prefix (such as `v`) is removed
- Leading zeros in delimited parts are truncated `XX.08` -> `XX.8`
- Tags are converted to a short form (`-alpha` -> `a0`)

For example:

- Pattern: `vYY.0M.0D[-RELEASE]`
- Version: `v20.08.02-beta`
- PEP440 : `20.8.2b0`

It may not be obvious to everyone that `v20.08.02-beta` is the same `20.8.2b0` on pypi. To avoid this confusion, you should choose a pattern which is always in a normalized form or as close to it as possible.

A further consideration for the choice of your version format is that it may be processed by tools that *do not* interpret it as a version number, but treat it just like any other string. It may also be confusing to your users if they a list of version numbers, sorted lexicographically by some tool (e.g. from `git tags`) and versions are not listed in order of their release as here:

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

### Pattern Examples

<!-- BEGIN pattern_examples -->

|             pattern             |               examples              | PEP440 | lexico. |
|---------------------------------|-------------------------------------|--------|---------|
| `MAJOR.MINOR.PATCH[PYTAGNUM]`   | `0.13.10          0.16.10rc1`       | yes    | no      |
| `MAJOR.MINOR[.PATCH[PYTAGNUM]]` | `1.11             0.3.0b5`          | yes    | no      |
| `YYYY.BUILD[PYTAGNUM]`          | `2020.1031        2020.1148a0`      | yes    | yes     |
| `YYYY.BUILD[-RELEASE]`          | `2021.1393-beta   2022.1279`        | no     | yes     |
| `YYYY.INC0[PYTAGNUM]`           | `2020.10          2021.12b2`        | yes    | no      |
| `YYYY0M.PATCH[-RELEASE]`        | `202005.12        202210.15-beta`   | no     | no¹     |
| `YYYY0M.BUILD[-RELEASE]`        | `202106.1071      202106.1075-beta` | no     | yes     |
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

- Does it start on a Monday or a Sunday?
- Range from 0-52 or 1-53 ?
- At the beginning/end of the year, do you have partial weeks or do you have a week that span multiple years?
- If a week spans multiple years, what is the year number?

If you use `VV`/`0V`, be aware that you cannot also use `YYYY`.
Instead use `GGGG`. This is to avoid an edge case where your version
number would run backwards if it was created around New Year.


<!-- BEGIN weeknum_example -->

```
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

The fastest way to setup the configuration for project is to use `calver init`.

```shell
$ pip install python-calver
...
Installing collected packages: click lexid pathlib2 typing toml python-calver
Successfully installed python-calver-2020.1041b0

$ cd myproject
~/myproject/
$ calver init --dry
Exiting because of '-d/--dry'. Would have written to calver.toml:

    [calver]
    current_version = "v202010.1001-alpha"
    version_pattern = "vYYYY0M.BUILD[-RELEASE]"
    commit_message = "bump version to {new_version}"
    commit = true
    tag = true
    push = true

    [calver.file_patterns]
    "README.md" = [
        "{version}",
        "{pep440_version}",
    ]
    "calver.toml" = [
        'current_version = "{version}"',
    ]
```

If you already have configuration file in your project (such as a `setup.cfg` file), then `calver init` will update that file instead.

```
~/myproject
$ calver init
Updated setup.cfg
```

Your `setup.cfg` may now look something like this:

```ini
[calver]
current_version = "2019.1001-alpha"
version_pattern = "YYYY.BUILD[-RELEASE]"
commit_message = "bump version to {new_version}"
commit = True
tag = True
push = True

[calver:file_patterns]
setup.cfg =
    current_version = "{version}"
setup.py =
    "{pep440_version}",
README.md =
    {version}
    {pep440_version}
```

For the entries in `[pycalver:file_patterns]` you can expect two failure modes:

- A pattern won't match a version number in the associated file.
- A pattern will match something it shouldn't (less likely).

To debug such issues, you can use `pycalver grep` .

```
$ pycalver grep 'Copyright (c) 2018-YYYY' src/module/*.py
src/module/__init__.py
   3: #
   4: # Copyright (c) 2018-2020 Vandelay Industries - All rights reserved.
   5: # SPDX-License-Identifier: MIT

src/module/config.py
   3: #
   4: # Copyright (c) 2018-2020 Vandelay Industries - All rights reserved.
   5: # SPDX-License-Identifier: MIT
```

Of course, you may not get the pattern correct right away. If your pattern is not found, `pycalver grep` will show an error message with the regular expression it uses, to help you debug the issue.

```
$ pycalver grep 'Copyright 2018-YYYY' src/pycalver/*.py
ERROR   - Pattern not found: 'Copyright 2018-YYYY'
# https://regex101.com/?flavor=python&flags=gmx&regex=Copyright%5B%20%5D2018%5C-%0A%28%3FP%3Cyear_y%3E%5B1-9%5D%5B0-9%5D%7B3%7D%29
re.compile(r"""
    Copyright[ ]2018\-
    (?P<year_y>[1-9][0-9]{3})
""", flags=re.VERBOSE)
```



Let's say you want to keep a badge your README.md up to date.

```
$ pycalver grep --version-pattern='vYYYY0M.BUILD[-RELEASE]' 'img.shields.io/static/v1.svg?label=PyCalVer&message={version}&color=blue' README.md

  61:
  62: [img_version]: https://img.shields.io/static/v1.svg?label=PyCalVer&message=v202010.1040-beta&color=blue
  63: [url_version]: https://pypi.org/org/package/

Found 1 match for pattern 'img.shields.io/static/v1.svg?label=PyCalVer&message=vYYYY0M.BUILD[-RELEASE]&color=blue' in README.md
```



This probably won't cover all version numbers present in your project, so you will have to manually add entries to `pycalver:file_patterns`. To determine what to add, you can use  `pycalver grep` :

```
$ pycalver grep 'Copyright (c) 2018-YYYY' src/project/*.py
```



Something like the following may illustrate additional changes you might need to make.

```ini
[pycalver:file_patterns]
setup.cfg =
    current_version = {version}
setup.py =
    version="{pep440_version}"
src/mymodule_v*/__init__.py =
    __version__ = "{version}"
README.md =
    [CalVer {version}]
    img.shields.io/static/v1.svg?label=CalVer&message={version}&color=blue
```

To see if a pattern is found, you can use `pycalver bump --dry`, which will
leave your project files untouched and only show you a diff of the changes
it would have made.

```shell
$ pycalver bump --dry --no-fetch
INFO    - Old Version: v201901.1001-beta
INFO    - New Version: v201902.1002-beta
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

If there is no match for a pattern, bump will report an error.

```shell
# TODO (mb 2020-08-29):  update regex pattern
$ pycalver bump --dry --no-fetch
INFO    - Old Version: v201901.1001-beta
INFO    - New Version: v201902.1002-beta
ERROR   - No match for pattern 'img.shields.io/static/v1.svg?label=CalVer&message={version}&color=blue'
ERROR   - Pattern compiles to regex 'img\.shields\.io/static/v1\.svg\?label=CalVer&message=(?P<year_y>\d{4})(?P<month>(?:0[0-9]|1[0-2]))\.(?P<bid>\d{4,})(?:-(?P
<tag>(?:alpha|beta|dev|rc|post|final)))?)&color=blue'
```

The internally used regular expression is also shown, which you can use to debug the issue, for example on [regex101.com](https://regex101.com/r/ajQDTz/2).

TODO Update above link
### Legacy Patterns

> These patterns use curly braces `{}` and were the initial implementation. They are still supported and still follow their original semantics.

The `pycalver:file_patterns` section of the configuration uses a different set
of placeholders and does not use curly braces to mark placeholders. It is still
supported, but we don't recomend you use it.

Available placeholders are:


|     placeholder     |  range / example(s) |     comment     |
|---------------------|---------------------|-----------------|
| `{year}`            | 2019...             | `%Y`            |
| `{yy}`              | 18, 19..99, 01, 02  | `%y`            |
| `{quarter}`         | 1, 2, 3, 4          |                 |
| `{month}`           | 09, 10, 11, 12      | `%m`            |
| `{iso_week}`        | 00..53              | `%W`            |
| `{us_week}`         | 00..53              | `%U`            |
| `{dom}`             | 01..31              | `%d`            |
| `{doy}`             | 001..366            | `%j`            |
| `{build}`           | .1023               | lexical id      |
| `{build_no}`        | 1023, 20345         | ...             |
| `{release}`         | -alpha, -beta, -rc  | --release=<tag> |
| `{release_tag}`     | alpha, beta, rc     | ...             |



|     placeholder     |  range / example(s) |     comment     |
|---------------------|---------------------|-----------------|
| `{pycalver}`        | v201902.1001-beta   |                 |
| `{pep440_pycalver}` | 201902.1b0          |                 |
| `{semver}`          | 1.2.3               |                 |


### Pattern Usage

<!-- TODO (mb 2020-09-24):  UPDATE USAGE -->

There are some limitations to keep in mind:

 1. A version string cannot span multiple lines.
 2. Characters generated by a placeholder cannot be escaped.
 3. The timezone is always UTC.

The lack of escaping may for example be an issue with badge URLs.
You may want to put the following text in your README.md (note
that shields.io parses the two "-" dashes before `beta` as one
literal "-"):

```
https://img.shields.io/badge/myproject-v202010.1116--beta-blue.svg
```

While you could use the following pattern, which will work fine for a
while:

```ini
README.md =
    /badge/myproject-{vYYYY0M.BUILD[--RELEASE]}-blue.svg
```

Eventually this will break, when you do a `final` release, at
which point the following will be put in your README.md:

```
https://img.shields.io/badge/myproject-v202010.1117--final-blue.svg
```

When what you probably wanted was this (with the `--final` tag omitted):

```
https://img.shields.io/badge/myproject-v202010.1117-blue.svg
```




### Version State

The "current version" is considered global state that needs to be
stored somewhere. Typically this might be stored in a `VERSION`
file, or some other file which is part of the repository. This
creates the risk that parallel branches can have different
states. If the "current version" were defined only by files in
the local checkout, the same version might be generated for
different commits.

To avoid this issue, pycalver treats VCS tags as the canonical /
[SSOT][url_ssot] for the most recent version and attempts to
change this state in the most atomic way possible. This is why
some actions of the `pycalver` command can take a while, as it is
synchronizing with the remote repository to get the most recent
versions and to push any new version tags as soon as possible.

[url_ssot]: https://en.wikipedia.org/wiki/Single_source_of_truth



### The Current Version

The current version that will be bumped is defined either as

 - Typically: The lexically largest git/mercurial tag which matches the
   `version_pattern` from your config.
 - Initially: Before any tags have been created (or you're not using a
   supported VCS), the value of `pycalver.current_version` in `setup.cfg` /
   `pyproject.toml` / `pycalver.toml`.

As part of doing `pycalver bump` and `pycalver show`, your local VCS
index is updated using `git fetch --tags`/`hg pull`.

```shell
$ time pycalver show --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Working dir version        : v202010.1018
INFO    - Latest version from git tag: v202010.1019-beta
Current Version: v202010.1019-beta
PEP440         : 202010.1019b0

real    0m4,254s

$ time pycalver show --verbose --no-fetch
...
real    0m0,840s
```

Here we see that:

- The VCS had a newer version than we had locally.
- It took 4 seconds to fetch the tags from the remote repository.

This approach reduces the risk that new tags are unknown locally and makes it
less likely that the same version string is generated for different commits,
which would result in an ambiguous version tag. This can happen if multiple
maintainers produce a release at the same time or if a build system is triggered
multiple times and multiple builds run concurrently to each other.

For a small project (with only one maintainer and no build system) this is a
non-issue and you can always use `-n/--no-fetch` to skip updating the tags.


### Bump It Up

To increment the current version and publish a new version, you can use the
`pycalver bump` sub-command. `bump` is configured in the `pycalver` config
section:

```ini
[pycalver]
current_version = "v202010.1006-beta"
version_pattern = "vYYYY0M.BUILD[-RELEASE]"
commit_message = "bump version to {new_version}"
commit = True
tag = True
push = True
```

This configuration is appropriate to create a commit which

1. contains the changes to the version strings,
2. contains no other changes (unrelated to bumping the version),
3. is tagged with the new version,
4. has a version tag that is unique in the repository.

In order to make sure only changes to version strings are in the commit,
you need to make sure you have a clean VCS checkout when you invoke
`pycalver bump`.

The steps performed by `bump` are:

0. Check that your repo doesn't have any local changes.
1. *Fetch* the most recent global VCS tags from origin
   (`-n`/`--no-fetch` to disable).
2. Generate a new version, incremented from the current version.
3. Update version strings in all files configured in `file_patterns`.
4. *Commit* the updated version strings.
5. *Tag* the new commit.
6. *Push* the new commit and tag.

Again, you can use `-d/--dry` to inspect the changes first.

```
$ pycalver bump --dry
--- setup.cfg
+++ setup.cfg
@@ -65,7 +65,7 @@

 [pycalver]
-current_version = v202010.1005-beta
+current_version = v202010.1006-beta
 version_pattern = "vYYYY0M.BUILD[-RELEASE]"
 commit_message = "bump version to {new_version}"
 commit = True
...
```

If everything looks OK, you can do `pycalver bump`.

```
$ pycalver bump --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Old Version: v202010.1005-beta
INFO    - New Version: v202010.1006-beta
INFO    - git commit --message 'bump version to v202010.1006-beta'
INFO    - git tag --annotate v202010.1006-beta --message v202010.1006-beta
INFO    - git push origin v202010.1006-beta
```

### Config Parameters

<!-- TODO (mb 2020-09-24): descriptions -->


| Config Parameter  | Type     | Description                  |
| ----------------- | -------- | ---------------------------- |
| `current_version` | string   |                              |
| `version_pattern` | string   |                              |
| `commit_message`  | string   | Template for commit message¹ |
| `commit`          | boolean  |                              |
| `tag`             | boolean² |                              |
| `push`            | boolean² |                              |

- ¹ Available placeholders: `{new_version}`, `{old_version}`, `{new_version_pep440}`, `{old_version_pep440}`
- ² Requires `commit = True`


## The PyCalVer Format

The PyCalVer format for version strings has three parts:

```

   o Year of Release
   |      o Sequential Build Number
   |      |      o Release Tag (optional)
   |      |      |
 --+--  --+--  --+--
 v2020  .1001  -beta

```

Some examples:

```
2017.1001-alpha
2017.1027-beta
2018.1031
2018.1032-post
...
2022.28133
2022.28134
```

This format was chosen in part to be distinctive from
others, so that users of your package can see at a glance that your project
will strive to maintain the one semantic that really matters: **newer is
better**.

To convince you of the merits of not breaking things, here are some
resources which PyCalVer was inspired by:

 - ["Speculation" talk by Rich
   Hicky](https://www.youtube.com/watch?v=oyLBGkS5ICk)
 - [Designing a Version by Mahmoud
   Hashemi](http://sedimental.org/designing_a_version.html)
 - [calver.org](https://calver.org/)
 - ["The cargo cult of versioning" by Kartik
   Agaram](http://akkartik.name/post/versioning)
 - The [bumpversion][bumpversion_ref] project, upon which
   PyCalVer is partially based.
 - ["Our Software Dependency Problem" by Russ Cox](https://research.swtch.com/deps)


### Parsing

These version strings can be parsed with the following regular expression:

```python
import re

# https://regex101.com/r/fnj60p/14
PYCALVER_PATTERN = r"""
\b
(?P<pycalver>
    (?P<vYYYY>
       v                    # "v" version prefix
       (?P<year>\d{4})
    )
    (?P<build>
        \.                  # "." build nr prefix
        (?P<build_no>\d{4,})
    )
    (?P<release>
        \-                  # "-" release prefix
        (?P<release_tag>alpha|beta|dev|rc|post)
    )?
)(?:\s|$)
"""
PYCALVER_REGEX = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)

version_str = "v2017.1001-alpha"
version_match = PYCALVER_REGEX.match(version_str)

assert version_match.groupdict() == {
    "pycalver"   : "v2017.1001-alpha",
    "vYYYY0M"    : "v2017",
    "year"       : "2017",
    "build"      : ".1001",
    "build_no"   : "1001",
    "release"    : "-alpha",
    "release_tag": "alpha",
}

version_str = "v201712.1033"
version_match = PYCALVER_REGEX.match(version_str)

assert version_match.groupdict() == {
    "pycalver"   : "v2017.1033",
    "vYYYY"      : "v2017",
    "year"       : "2017",
    "build"      : ".1033",
    "build_no"   : "1033",
    "release"    : None,
    "release_tag": None,
}
```

### Incrementing Behaviour

To see how version strings are incremented, we can use
`calver test`:

```shell
$ calver test v2018.1033-beta
New Version: v2019.1034-beta
PEP440     : 2019.1034b0
```

This is the simple case:

 - The calendar component is updated to the current year and month.
 - The build number is incremented by 1.
 - The optional release tag is preserved as is.

You can explicitly update the release tag by using the `--release=<tag>` argument:

```shell
$ calver test v2018.1033-alpha --release=beta
New Version: v2019.1034-beta
PEP440     : 2019.1034b0

$ calver test v2019.1034-beta --release=final
New Version: v2019.1035
PEP440     : 2019.1035
```

To maintain lexical ordering of version numbers, the version number is padded with extra zeros using [Lexical Ids][url_pypi_lexid].
This means that the expression `older_id < newer_id` will always be true, whether you are dealing with integers or strings.

[url_pypi_lexid]: https://pypi.org/project/lexid/



## Semantics of PyCalVer

> Disclaimer: This section is of course only aspirational. Nothing will
> stop a package maintainer from publishing updates that violate the
> semantics presented here.


### Pitch

- dates are good information
    - how old is the software
    - is the software maintained
    - is my dependency outdated
    - can I trust an update?


### blah

PyCalVer places a greater burden on package maintainers than SemVer.
Backward incompatibility is not encoded in the version string, because
**maintainers should not intentionally introduce breaking changes**. This
is great for users of a package, who can worry a bit less about an update
causing their project to break. A paranoid user can of course still pin to
a known good version, and freezing dependencies for deployments is still a
good practice, but for development, users ideally shouldn't need any
version specifiers in their requirements.txt. This way they always get the
newest bug fixes and features.

Part of the reason for the distinctive PyCalVer version string, is for
users to be able to recognize, just from looking at the version string,
that a package comes with the promise (or at least aspiration) that it
won't break, that it is safe for users to update. Compare this to a SemVer
version string, where maintainers explicitly state that an update _might_
break their program and that they _may_ have to do extra work after
updating and even if it hasn't in the past, the package maintainers
anticipate that they might make such breaking changes in the future.

In other words, the onus is on the user of a package to update their
software, if they want to update to the latest version of a package. With
PyCalVer the onus is on package maintainer to maintain backward
compatibility.

Ideally users can trust the promise of a maintainer that the following
semantics will always be true:

 - Newer is compatible.
 - Newer has fewer bugs.
 - Newer has more features.
 - Newer has equal or better performance.

Alas, the world is not ideal. So how do users and maintainers deal with changes
that violate these promises?


### Intentional Breaking Changes

> Namespaces are a honking great idea
> - let's do more of those!
>
> - The Zen of Python

If you must make a breaking change to a package, **instead of incrementing a
number**, the recommended approach with PyCalVer is to **create a whole new
namespace**. Put differently, the major version becomes part of the name of the
module or even of the package. Typically you might add a numerical suffix, eg.
`mypkg -> mypkg2`.

In the case of python distributions, you can include multiple module
packages like this.

```python
# setup.py
setuptools.setup(
    name="my-package",
    license="MIT",
    packages=["mypkg", "mypkg2"],
    package_dir={"": "src"},
    ...
)
```

In other words, you can ship older versions side by side with newer ones,
and users can import whichever one they need. Alternatively you can publish
a new package distribution, with new namespace, but please consider also
renaming the module.

```python
# setup.py
setuptools.setup(
    name="my-package-v2",
    license="MIT",
    packages=["mypkg2"],
    package_dir={"": "src"},
    ...
)
```

Users will have an easier time working with your package if `import mypkg2`
is enough to determine which version of your project they are using. A further
benefit of creating multiple modules is that users can import both old and
new modules in the same environment and can use some packages which depend
on the old version as well as some that depend on the new version. The
downside for users, is that they may have to do minimal changes to their
code, even if the breaking change did not affect them.

```diff
- import mypkg
+ import mypkg2

  def usage_code():
-     mypkg.myfun()
+     mypkg2.myfun()
```


### Costs and Benefits

If this seems like overkill because it's a lot of work for you as a
maintainer, consider first investing some time in your tools, so you
minimize future work required to create new packages. I've [done this for
my personal projects][bootstrapit_ref], but you may find [other
approaches][cookiecutter_ref] to be more appropriate for your use.

If this seems like overkill because you're not convinced that imposing a
very small burden on users is such a big deal, consider that your own
projects may indirectly depend on dozens of libraries which you've never
even heard of. If every maintainer introduced breaking changes only once
per year, users who depend on only a dozen libraries would be dealing with
packaging issues every month! In other words: *Breaking things is a big
deal*. A bit of extra effort for a few maintainers seems like a fair trade
to lower the effort imposed on many users, who would be perfectly happy to
continue using the old code until _they_ decide when to upgrade.


### Unintentional Breaking Changes

The other kind of breaking change is the non-intentional kind, otherwise
known as a "bug" or "regression". Realize first of all, that it is
impossible for any versioning system to encode that this has happened:
Since the maintainer isn't knowingly introducing a bug they naturally can't
update their version numbers to reflect what they don't know about. Instead
we have to deal with these issues after the fact.

The first thing a package maintainer can do is to minimize the chance of
inflicting buggy software on users. After any non-trivial (potentially breaking)
change, it is a good practice to first create an `-alpha`/`-beta`/`-rc` release.
These so called `--pre` releases are intended to be downloaded only by the few
and the brave: Those who are willing to participate in testing. After any issues
are ironed out with the `--pre` releases, a `final` release can be made for the
wider public.

Note that the default behaviour of `pip install <package>` (without any version
specifier) is to download the latest `final` release. It will download a `--pre`
release *only* if

 1. no `final` release is available
 2. the `--pre` flag is explicitly used, or
 3. if the requirement specifier _explicitly_ includes the version number of a
    pre release, eg. `pip install mypkg==v202009.1007-alpha`.

Should a release include a bug (heaven forbid and despite all precautions),
then the maintainer should publish a new release which either fixes the bug
or reverts the change. If users previously downloaded a version of the
package which included the bug, they only have to do `pip install --upgrade
<package>` and the issue will be resolved.

Perhaps a timeline will illustrate more clearly:

```
v2020.1665       # last stable release
v2020.1666-beta  # pre release for testers
v2019.1667       # final release after testing

# bug is discovered which effects v2020.1666-beta and v2019.1667

v2019.1668-beta  # fix is issued for testers
v2019.1669       # fix is issued everybody

# Alternatively, revert before fixing

v2019.1668       # same as v2020.1665
v2019.1669-beta  # reintroduce change from v2020.1666-beta + fix
v2019.1670       # final release after testing
```

In the absolute worst case, a change is discovered to break backward
compatibility, but the change is nonetheless considered to be desirable. At that
point, a new release should be made to revert the change.

This allows 1. users who _were_ exposed to the breaking change to update to the
latest release and get the old (working) code again, and 2. users who _were not_
exposed to the breaking change to never even know anything was broken.

Remember that the goal is to always make things easy for users who have
your package as a dependency. If there is any issue whatsoever, all they
should have to do is `pip install --update`. If this doesn't work, they may
have to *temporarily* pin to a known good version, until a fixed release
has been published.

After this immediate fire has been extinguished, if the breaking change is
worth keeping, then **create a new module or even a new package**. This
package will perhaps have 99% overlap to the previous one and the old one
may eventually be abandoned.

```
mypkg  v2020.1665    # last stable release
mypkg  v2020.1666-rc # pre release for testers
mypkg  v2019.1667    # final release after testing period

# bug is discovered in v2020.1666-beta and v2019.1667

mypkg  v2019.1668    # same as v2020.1665

# new package is created with compatibility breaking code

mypkg2 v2019.1669    # same as v2019.1667
mypkg  v2019.1669    # updated readme, declaring support
                       # level for mypkg, pointing to mypgk2
                       # and documenting how to upgrade.
```


### Pinning is not a Panacea

Freezing your dependencies by using `pip freeze` to create a file with packages
pinned to specific version numbers is great to get a stable and repeatable
deployment.

The main problem with pinning is that it is another burden imposed on users,
and it is a burden which in practice only some can bear. The vast majority of
users either 1) pin their dependencies and update them without determining what
changed or if it is safe for them to update, or 2) pin their dependencies and
forget about them. In case 1 the only benefit is that users might at least be
aware of when an update happened, so they can perhaps correlate that a new bug
in their software might be related to a recent update. Other than that, keeping
tabs on dependencies and updating without diligence is hardly better than not
having pinned at all. In case 2, an insurmountable debt will pile up and the
dependencies of a project are essentially frozen in the past.

Yes, it is true that users will be better off if they have sufficient test
coverage to determine for themselves that their code is not broken even after
their dependencies are updated. It is also true however, that a package
maintainer is usually in a better position to judge if a change might cause
something to break.


### Zeno's 1.0 and The Eternal Beta

There are two opposite approaches to backward compatibility which find a
reflection in the version numbers they use. In the case of SemVer, if a
project has a commitment to backward compatibility, it may end up never
incriminating the major version, leading to the [Zeno 1.0
paradox][zeno_1_dot_0_ref]. On the other end are projects that avoid any
commitment to backward compatibility and forever keep the "beta" label.

Of course an unpaid Open Source developer *does not owe anybody a
commitment to backward compatibility*. Especially when a project is young
and going through major changes, such a commitment may not make any sense.
For these cases you can still use PyCalVer, just so long as there is a big
fat warning at the top of your README, that your project is not ready for
production yet.

Note that there is a difference between software that is considered to be
in a "beta" state and individual releases which have a `-beta` tag. These
do not mean the same thing. In the case of releases of python packages, the
release tag (`-alpha`, `-beta`, `-rc`) says something about the stability
of a *particular release*. This is similar ([perhaps
identical][pep_101_ref]) to the meaning of release tags used by the CPython
interpreter. A release tag is not a statement about the general stability
of the software as a whole, it is metadata about a particular release
artifact of a package, eg. a `.whl` file.


[setuptools_ref]: https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version

[pep_440_ref]: https://www.python.org/dev/peps/pep-0440/

[pep_440_normalzation_ref]: https://www.python.org/dev/peps/pep-0440/#id31

[zeno_1_dot_0_ref]: http://sedimental.org/designing_a_version.html#semver-and-release-blockage

[pep_101_ref]: https://www.python.org/dev/peps/pep-0101/

[bumpversion_ref]: https://github.com/peritus/bumpversion

[bootstrapit_ref]: https://gitlab.com/mbarkhau/bootstrapit

[cookiecutter_ref]: https://cookiecutter.readthedocs.io

