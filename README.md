# [PyCalVer: Automatic Calendar Versioning][repo_ref]

PyCalVer is a cli tool to search and replace version strings in the files of
your project.

By default PyCalVer uses a format that looks like this:
`v201812.0123-beta`, but it can be configured to generate version strings
in many formats, including SemVer and other CalVer variants.


Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer v201903.0028][version_img]][version_ref]
[![PyPI Releases][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![Build Status][build_img]][build_ref]
[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Code Style: sjfmt][style_img]][style_ref]


|                Name                 |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-09 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc -i gitlab README.md
-->


[](TOC)

- [Usage](#usage)
    - [Configuration](#configuration)
    - [Pattern Search and Replacement](#pattern-search-and-replacement)
    - [Examples](#examples)
    - [Version State](#version-state)
    - [The Current Version](#the-current-version)
    - [Bump It Up](#bump-it-up)
- [The PyCalVer Format](#the-pycalver-format)
    - [Parsing](#parsing)
    - [Incrementing Behaviour](#incrementing-behaviour)
    - [Lexical Ids](#lexical-ids)
- [Semantics of PyCalVer](#semantics-of-pycalver)
    - [Intentional Breaking Changes](#intentional-breaking-changes)
    - [Costs and Benefits](#costs-and-benefits)
    - [Unintentional Breaking Changes](#unintentional-breaking-changes)
    - [Pinning is not a Panacea](#pinning-is-not-a-panacea)
    - [Zeno's 1.0 and The Eternal Beta](#zeno-s-1-0-and-the-eternal-beta)

[](TOC)


## Usage

### Configuration

The fastest way to setup a project is to use `pycalver init`.


```shell
$ pip install pycalver
...
Installing collected packages: click pathlib2 typing toml six pycalver
Successfully installed pycalver-201903.28

$ pycalver --version
pycalver, version v201903.0028

$ cd myproject
~/myproject$ pycalver init --dry
WARNING - File not found: pycalver.toml
Exiting because of '--dry'. Would have written to pycalver.toml:

    [pycalver]
    current_version = "v201902.0001-alpha"
    version_pattern = "{pycalver}"
    commit = true
    tag = true
    push = true

    [pycalver.file_patterns]
    "README.md" = [
        "{version}",
        "{pep440_version}",
    ]
    "pycalver.toml" = [
        'current_version = "{version}"',
    ]
```

If you already have a `setup.cfg` file, the `init` sub-command will write to that
instead.

```
~/myproject$ ls
README.md  setup.cfg  setup.py

~/myproject$ pycalver init
WARNING - Couldn't parse setup.cfg: Missing [pycalver] section.
Updated setup.cfg
```

This will add the something like the following to your `setup.cfg`
(depending on what files already exist in your project):

```ini
# setup.cfg
[pycalver]
current_version = "v201902.0001-alpha"
version_pattern = "{pycalver}"
commit = True
tag = True
push = True

[pycalver:file_patterns]
setup.cfg =
    current_version = {version}
setup.py =
    "{version}",
    "{pep440_version}",
README.md =
    {version}
    {pep440_version}
```

This probably won't cover every version number used in your project and you
will have to manually add entries to `pycalver:file_patterns`. Something
like the following may illustrate additional changes you might need to
make.

```ini
[pycalver:file_patterns]
setup.cfg =
    current_version = {pycalver}
setup.py =
    version="{pep440_pycalver}"
src/mymodule_v*/__init__.py =
    __version__ = "{pycalver}"
README.md =
    [PyCalVer {calver}{build}{release}]
    img.shields.io/static/v1.svg?label=PyCalVer&message={pycalver}&color=blue
```

To see if a pattern is found, you can use `pycalver bump --dry`, which will
leave your project files untouched and only show you a diff of the changes
it would have made.

```shell
$ pycalver bump --dry --no-fetch
INFO    - Old Version: v201901.0001-beta
INFO    - New Version: v201902.0002-beta
--- README.md
+++ README.md
@@ -11,7 +11,7 @@

 [![Supported Python Versions][pyversions_img]][pyversions_ref]
-[![Version v201901.0001][version_img]][version_ref]
+[![Version v201902.0002][version_img]][version_ref]
 [![PyPI Releases][pypi_img]][pypi_ref]

--- src/mymodule_v1/__init__.py
+++ src/mymodule_v1/__init__.py
@@ -1,1 +1,1 @@
-__version__ = "v201901.0001-beta"
+__version__ = "v201902.0002-beta"

--- src/mymodule_v2/__init__.py
+++ src/mymodule_v2/__init__.py
@@ -1,1 +1,1 @@
-__version__ = "v201901.0001-beta"
+__version__ = "v201902.0002-beta"

--- setup.py
+++ setup.py
@@ -44,7 +44,7 @@
     name="myproject",
-    version="201901.1b0",
+    version="201902.2b0",
     license="MIT",
```

If there is no match for a pattern, bump will report an error.

```shell
$ pycalver bump --dry --no-fetch
INFO    - Old Version: v201901.0001-beta
INFO    - New Version: v201902.0002-beta
ERROR   - No match for pattern 'img.shields.io/static/v1.svg?label=PyCalVer&message={pycalver}&color=blue'
ERROR   - Pattern compiles to regex 'img\.shields\.io/static/v1\.svg\?label=PyCalVer&message=(?P<pycalver>v(?P<year>\d{4})(?P<month>(?:0[0-9]|1[0-2]))\.(?P<bid>\d{4,})(?:-(?P
<tag>(?:alpha|beta|dev|rc|post|final)))?)&color=blue'
```

The internally used regular expression is also shown, which you can use to debug the issue, for example on [regex101.com](https://regex101.com/r/ajQDTz/2).


### Pattern Search and Replacement

The `pycalver:file_patterns` section of the configuration is used both to search
and also to replace version strings in your projects files. Everything except
for valid placeholders is treated as literal text. Available placeholders are:


|     placeholder     |  range / example(s) |     comment     |
|---------------------|---------------------|-----------------|
| `{pycalver}`        | v201902.0001-beta   |                 |
| `{pep440_pycalver}` | 201902.1b0          |                 |
| `{year}`            | 2019...             | `%Y`            |
| `{yy}`              | 18, 19..99, 01, 02  | `%y`            |
| `{quarter}`         | 1, 2, 3, 4          |                 |
| `{month}`           | 09, 10, 11, 12      | `%m`            |
| `{iso_week}`        | 00..53              | `%W`            |
| `{us_week}`         | 00..53              | `%U`            |
| `{dom}`             | 01..31              | `%d`            |
| `{doy}`             | 001..366            | `%j`            |
| `{build}`           | .0123               | lexical id      |
| `{build_no}`        | 0123, 12345         | ...             |
| `{release}`         | -alpha, -beta, -rc  | --release=<tag> |
| `{release_tag}`     | alpha, beta, rc     | ...             |
| `{semver}`          | 1.2.3               |                 |
| `{MAJOR}`           | 1..9, 10..99, 100.. | --major         |
| `{MINOR}`           | 1..9, 10..99, 100.. | --minor         |
| `{PATCH}`           | 1..9, 10..99, 100.. | --patch         |


There are some limitations to keep in mind:

 1. A version string cannot span multiple lines.
 2. Characters generated by a placeholder cannot be escaped.
 3. The timezone is always UTC.

The lack of escaping may for example be an issue with badge URLs.
You may want to put the following text in your README.md (note
that shields.io parses the two "-" dashes before `beta` as one
literal "-"):

```
https://img.shields.io/badge/myproject-v201812.0116--beta-blue.svg
```

While you could use the following pattern, which will work fine for a
while:

```ini
README.md =
    /badge/myproject-v{year}{month}.{build_no}--{release_tag}-blue.svg
```

Eventually this will break, when you do a `final` release, at
which point the following will be put in your README.md:

```
https://img.shields.io/badge/myproject-v201812.0117--final-blue.svg
```

When what you probably wanted was this (with the `--final` tag omitted):

```
https://img.shields.io/badge/myproject-v201812.0117-blue.svg
```

### Examples

The easiest way to test a pattern is with the `pycalver test` sub-command.

```shell
$ pycalver test 'v18w01' 'v{yy}w{iso_week}'
New Version: v19w06
PEP440     : v19w06

$ pycalver test 'v18.01' 'v{yy}w{iso_week}'
ERROR   - Invalid version string 'v18.01' for pattern
  'v{yy}w{iso_week}'/'v(?P<yy>\d{2})w(?P<iso_week>(?:[0-4]\d|5[0-3]))'
ERROR   - Invalid version 'v18.01' and/or pattern 'v{yy}w{iso_week}'.
```

As you can see, each pattern is internally translated to a regular
expression.

The `pycalver test` sub-command accepts the same cli flags as `pycalver
bump` to update the components that are not updated automatically (eg.
based on the calendar).

```shell
$ pycalver test 'v18.1.1' 'v{yy}.{MINOR}.{PATCH}'
New Version: v19.1.1
PEP440     : 19.1.1

$ pycalver test 'v18.1.1' 'v{yy}.{MINOR}.{PATCH}' --patch
New Version: v19.1.2
PEP440     : 19.1.2

$ pycalver test 'v18.1.2' 'v{yy}.{MINOR}.{PATCH}' --minor
New Version: v19.2.0
PEP440     : 19.2.0

$ pycalver test 'v201811.0051-beta' '{pycalver}'
New Version: v201902.0052-beta
PEP440     : 201902.52b0

$ pycalver test 'v201811.0051-beta' '{pycalver}' --release rc
New Version: v201902.0052-rc
PEP440     : 201902.52rc0

$ pycalver test 'v201811.0051-beta' '{pycalver}' --release final
New Version: v201902.0052
PEP440     : 201902.52
```

Note that pypi/setuptools/pip will normalize version strings to a format
defined in [PEP440][pep_440_ref]. You can use a format that deviates from
this, just be aware that version strings processed by these tools will look
different.


### Version State

The "current version" is considered global state that needs to be
stored somewhere. Typically this might be stored in a `VERSION`
file, or some other file which is part of the repository. This
creates the risk that parallel branches can have different
states. If the "current version" were defined only by files in
the local checkout, the same version might be generated for
different commits.

To avoid this issue, pycalver treats VCS tags as the canonical /
[SSOT][ssot_ref] for the most recent version and attempts to
change this state in the most atomic way possible. This is why
some actions of the `pycalver` command can take a while, as it is
synchronizing with the remote repository to get the most recent
versions and to push any new version tags as soon as possible.


### The Current Version

The current version that will be bumped is defined either as

 - Typically: The lexically largest git/mercurial tag which matches the
   `version_pattern` from your config.
 - Initially: Before any tags have been created (or you're not using a
   supported VCS), the value of `pycalver.current_version` in `setup.cfg` /
   `pyproject.toml` / `pycalver.toml`.

As part of doing `pycalver bump`, your local VCS index is updated using
`git fetch --tags`/`hg pull`. This reduces the risk that some tags are
unknown locally and makes it less likely that the same version string is
generated for different commits, which would result in an ambiguous version
tag. This can happen if multiple maintainers produce a release at the same
time or if a build system is triggered multiple times and multiple builds
run concurrently to each other. For a small project (with only one
maintainer and no build system) this is a non-issue and you can always use
`-n/--no-fetch` to skip updating the tags.

```shell
$ time pycalver show --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Working dir version        : v201812.0018
INFO    - Latest version from git tag: v201901.0019-beta
Current Version: v201901.0019-beta
PEP440         : 201901.19b0

real    0m4,254s

$ time pycalver show --verbose --no-fetch
...
real    0m0,840s
```


### Bump It Up

To increment the current version and publish a new version, you can use the
`pycalver bump` sub-command. `bump` is configured in the `pycalver` config
section:

```ini
[pycalver]
current_version = "v201812.0006-beta"
version_pattern = "{pycalver}"
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

Again, you can use `--dry` to inspect the changes first.

```
$ pycalver bump --dry
--- setup.cfg
+++ setup.cfg
@@ -65,7 +65,7 @@

 [pycalver]
-current_version = v201812.0005-beta
+current_version = v201812.0006-beta
 commit = True
 tag = True
 push = True
...
```

If everything looks OK, you can do `pycalver bump`.

```
$ pycalver bump --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
INFO    - Old Version: v201812.0005-beta
INFO    - New Version: v201812.0006-beta
INFO    - git commit --file /tmp/tmpph_npey9
INFO    - git tag --annotate v201812.0006-beta --message v201812.0006-beta
INFO    - git push origin v201812.0006-beta
```


## The PyCalVer Format

The PyCalVer format for version strings has three parts:

```

    o Year and Month of Release
    |       o Sequential Build Number
    |       |      o Release Tag (optional)
    |       |      |
 ---+---  --+--  --+--
 v201812  .0123  -beta


```

Some examples:

```
v201711.0001-alpha
v201712.0027-beta
v201801.0031
v201801.0032-post
...
v202207.18133
v202207.18134
```

This slightly verbose format was chosen in part to be distinctive from
others, so that users of your package can see at a glance that your project
will strive to maintain the one semantic that really matters: **newer ==
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

# https://regex101.com/r/fnj60p/10
PYCALVER_PATTERN = r"""
\b
(?P<pycalver>
    (?P<vYYYYMM>
       v                    # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
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

version_str = "v201712.0001-alpha"
version_match = PYCALVER_REGEX.match(version_str)

assert version_match.groupdict() == {
    "pycalver"   : "v201712.0001-alpha",
    "vYYYYMM"    : "v201712",
    "year"       : "2017",
    "month"      : "12",
    "build"      : ".0001",
    "build_no"   : "0001",
    "release"    : "-alpha",
    "release_tag": "alpha",
}

version_str = "v201712.0033"
version_match = PYCALVER_REGEX.match(version_str)

assert version_match.groupdict() == {
    "pycalver"   : "v201712.0033",
    "vYYYYMM"    : "v201712",
    "year"       : "2017",
    "month"      : "12",
    "build"      : ".0033",
    "build_no"   : "0033",
    "release"    : None,
    "release_tag": None,
}
```

### Incrementing Behaviour

To see how version strings are incremented, we can use
`pycalver test`:

```shell
$ pycalver test v201801.0033-beta
New Version: v201902.0034-beta
PEP440     : 201902.34b0
```

This is the simple case:

 - The calendar component is updated to the current year and
   month.
 - The build number is incremented by 1.
 - The optional release tag is preserved as is.

You can explicitly update the release tag by using the
`--release=<tag>` argument:

```shell
$ pycalver test v201801.0033-alpha --release=beta
New Version: v201902.0034-beta
PEP440     : 201902.34b0

$ pycalver test v201902.0034-beta --release=final
New Version: v201902.0035
PEP440     : 201902.35
```

To maintain lexical ordering of version numbers, the version number is padded
with extra zeros (see [Lexical Ids](#lexical-ids) ).


### Lexical Ids

The build number padding may eventually be exhausted. In order to preserve
lexical ordering, build numbers for the `{build_no}` pattern are
incremented in a special way. Examples will perhaps illustrate more
clearly.

```python
"0001"
"0002"
"0003"
...
"0999"
"11000"
"11001"
...
"19998"
"19999"
"220000"
"220001"
```

What is happening here is that the left-most digit is incremented
early/preemptively. Whenever the left-most digit would change, the padding
of the id is expanded through a multiplication by 11.

```python
>>> prev_id  = "0999"
>>> num_digits = len(prev_id)
>>> num_digits
4
>>> prev_int = int(prev_id, 10)
>>> prev_int
999
>>> maybe_next_int = prev_int + 1
>>> maybe_next_int
1000
>>> maybe_next_id = f"{maybe_next_int:0{num_digits}}"
>>> maybe_next_id
"1000"
>>> is_padding_ok = prev_id[0] == maybe_next_id[0]
>>> is_padding_ok
False
>>> if is_padding_ok:
...     # normal case
...     next_id = maybe_next_id
... else:
...     # extra padding needed
...     next_int = maybe_next_int * 11
...     next_id  = str(next_int)
>>> next_id
"11000"
```

This behaviour ensures that the following semantic is always preserved:
`new_version > old_version`. This will be true, regardless of padding
expansion. To illustrate the issue this solves, consider what would happen
if we did not expand the padding and instead just incremented numerically.

```python
"0001"
"0002"
"0003"
...
"0999"
"1000"
...
"9999"
"10000"
```

Here we eventually run into a build number where the lexical ordering is
not preserved, since `"10000" > "9999" == False` (because the string `"1"`
is lexically smaller than `"9"`). With large enough padding this may be a
non issue, but it's better to not have to think about it.

Just as an example of why lexical ordering is a nice property to have,
there are lots of software which read git tags, but which have no logic to
parse version strings. This software can nonetheless order the version tags
correctly using commonly available lexical ordering. At the most basic
level it can allow you to use the UNIX `sort` command, for example to parse
VCS tags.


```shell
$ printf "v0.9.0\nv0.10.0\nv0.11.0\n" | sort
v0.10.0
v0.11.0
v0.9.0

$ printf "v0.9.0\nv0.10.0\nv0.11.0\n" | sort -n
v0.10.0
v0.11.0
v0.9.0

$ printf "0998\n0999\n11000\n11001\n11002\n" | sort
0998
0999
11000
11001
11002
```

This sorting even works correctly in JavaScript!

```
> var versions = ["11002", "11001", "11000", "0999", "0998"];
> versions.sort();
["0998", "0999", "11000", "11001", "11002"]
```


## Semantics of PyCalVer

> Disclaimer: This section can of course only be aspirational. There is nothing
> to prevent package maintainers from publishing packages with different
> semantics than what is presented here.

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
is enough to determine which version of your project are using. A further
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
    pre release, eg. `pip install mypkg==v201812.0007-alpha`.

Should a release include a bug (heaven forbid and despite all precautions),
then the maintainer should publish a new release which either fixes the bug
or reverts the change. If users previously downloaded a version of the
package which included the bug, they only have to do `pip install --upgrade
<package>` and the issue will be resolved.

Perhaps a timeline will illustrate more clearly:

```
v201812.0665       # last stable release
v201812.0666-beta  # pre release for testers
v201901.0667       # final release after testing

# bug is discovered which effects v201812.0666-beta and v201901.0667

v201901.0668-beta  # fix is issued for testers
v201901.0669       # fix is issued everybody

# Alternatively, revert before fixing

v201901.0668       # same as v201812.0665
v201901.0669-beta  # reintroduce change from v201812.0666-beta + fix
v201901.0670       # final release after testing
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
mypkg  v201812.0665    # last stable release
mypkg  v201812.0666-rc # pre release for testers
mypkg  v201901.0667    # final release after testing period

# bug is discovered in v201812.0666-beta and v201901.0667

mypkg  v201901.0668    # same as v201812.0665

# new package is created with compatibility breaking code

mypkg2 v201901.0669    # same as v201901.0667
mypkg  v201901.0669    # updated readme, declaring support
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


[repo_ref]: https://gitlab.com/mbarkhau/pycalver

[setuptools_ref]: https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version

[ssot_ref]: https://en.wikipedia.org/wiki/Single_source_of_truth

[pep_440_ref]: https://www.python.org/dev/peps/pep-0440/

[zeno_1_dot_0_ref]: http://sedimental.org/designing_a_version.html#semver-and-release-blockage

[pep_101_ref]: https://www.python.org/dev/peps/pep-0101/

[bumpversion_ref]: https://github.com/peritus/bumpversion

[bootstrapit_ref]: https://gitlab.com/mbarkhau/bootstrapit

[cookiecutter_ref]: https://cookiecutter.readthedocs.io


[build_img]: https://gitlab.com/mbarkhau/pycalver/badges/master/pipeline.svg
[build_ref]: https://gitlab.com/mbarkhau/pycalver/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/pycalver/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/pycalver/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/pycalver/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: https://mbarkhau.gitlab.io/pycalver/mypycov

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[downloads_img]: https://pepy.tech/badge/pycalver/month
[downloads_ref]: https://pepy.tech/project/pycalver

[version_img]: https://img.shields.io/static/v1.svg?label=PyCalVer&message=v201903.0028&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/pycalver/#files

[pyversions_img]: https://img.shields.io/pypi/pyversions/pycalver.svg
[pyversions_ref]: https://pypi.python.org/pypi/pycalver

