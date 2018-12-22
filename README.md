# [PyCalVer: Automatic CalVer Versioning for Python Packages][repo_ref]

PyCalVer is for projects that only have one semantic: newer ==
better. PyCalVer version strings are compatible with python
packaging software [setuptools][setuptools_ref] and
[PEP440][pep_440_ref], but can in principle be used with any
project.


Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer v201812.0017][version_img]][version_ref]
[![PyPI Releases][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Style: sjfmt][style_img]][style_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Build Status][build_img]][build_ref]


|                Name                 |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-09 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc -i gitlab README.md
-->


[](TOC)

  - [Introduction](#introduction)
  - [Semantics of PyCalVer](#semantics-of-pycalver)
      - [Breaking Changes](#breaking-changes)
      - [Zeno's 1.0 and the Eternal Beta](#zenos-10-and-the-eternal-beta)
      - [Version String Format](#version-string-format)
      - [Incrementing Behaviour](#incrementing-behaviour)
  - [Usage](#usage)
      - [Configuration](#configuration)
      - [Pattern Search and Replacement](#pattern-search-and-replacement)
      - [Bump It Up](#bump-it-up)
      - [Version State](#version-state)
      - [Lexical Ids](#lexical-ids)

[](TOC)


## Introduction

The PyCalVer package provides the `pycalver` command to generate
version strings. The version strings have three parts:

```

    o Year and Month of Build
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

PyCalVer is inspired by:

 - ["Speculation" talk by Rich
   Hicky](https://www.youtube.com/watch?v=oyLBGkS5ICk)
 - [Designing a Version by Mahmoud
   Hashemi](http://sedimental.org/designing_a_version.html)
 - [calver.org](https://calver.org/)
 - ["The cargo cult of versioning" by Kartik
   Agaram](http://akkartik.name/post/versioning)
 - The [bumpversion][bumpversion_ref] project, upon which
   PyCalVer is partially based.

If you are familiar with these, feel free to skip ahead to
[Usage](#usage)


## Semantics of PyCalVer

> Disclaimer: This section is aspirational and of course there
> is nothing to prevent package maintainers from publishing
> packages with different semantics than what is laid out here.

PyCalVer places a greater burden on package maintainers than
SemVer. Backward incompatibility is not encoded, because
maintainers should not make any breaking changes. This is great
for users of a package, who can worry a bit less about an update
breaking their project. If they're paranoid, they can of course
still pin to known good versions, but ideally they don't need
version specifier in their requirements.txt so they always get
the latest bug fixes and features. Ideally users can trust the
promise of a maintainer that the following semantics will always
be true:

 - Newer is compatible.
 - Newer has fewer bugs.
 - Newer has more features.
 - Newer has similar or better performance.

The world is not ideal of course, so how do users and
maintainers deal with changes that might violate these promises?


### Breaking Changes

> Namespaces are one honking great idea
> -- let's do more of those!

If you must make a breaking change to a package, *instead of
incrementing a number*, the recommended approach with PyCalVer
is to *create a whole new package*. Put differently, the major
version becomes part of the package/module namespace. Typically
you might add a numerical suffix, eg. `mypkg -> mypkg2`.

The other kind of breaking change is the non-intentional kind,
otherwise known as a bug. Realize first of all, that it is
impossible for any versioning system to encode that this has
happened: Since the maintainer isn't knowingly introducing a bug
they naturally won't set a version to reflect something they
don't know about. Instead we have to deal with this issue after
the fact.

The first thing a package maintainer can do is to minimize the
chance of inflicting buggy software on users. After any
non-trivial (maybe unsafe) change, create a new
`-alpha`/`-beta`/`-rc` release. These so called `--pre` releases
are downloaded only by the few and the brave, who are willing to
participate in testing. After any any issues are ironed with the
`--pre` releases, a `final` release can be made for more
regular/conservative users.

Note that the default behaviour of `pip install <package>`
(without any version specifier) is to download the latest
`final` release. It will download a `--pre` release *only* if

 1. there is no `final` release available yet
 2. the `--pre` flag is explicitly used, or
 3. if the requirement specifier explicitly includes the version
    number of a pre release, eg. `pip install
    mypkg==v201812.0007-alpha`.

Should a release include a bug (heaven forbid and despite all
precautions), then the maintainer should publish a new release
which either fixes the or reverts the change. It is important
that the new release have a greater version than the release
that contained the issue and that it use the same release
suffix. If users downloaded a version of the package which
included the bug, they only have to do `pip install --upgrade
<package>` and the issue will be resolved.

Perhaps a timeline will illustrate more clearly:

```
v201812.0665          # last stable release
v201812.0666-beta     # pre release for testers
v201901.0667          # final release after testing

# bug is discovered which effects v201812.0666-beta and v201901.0667

v201901.0668-beta     # fix is issued for testers
v201901.0669          # fix is issued everybody

# Alternatively, revert before fixing

v201901.0668          # identical code to v201812.0665
v201901.0669-beta     # reintroduce change from v201812.0666-beta + fix
v201901.0670          # final release after testing
```

In the absolute worst case, a change is discovered to break
backward compatibility, but the change is still considered to be
desirable. At that point, a new release should be made to revert
the change. This way:

 - users who were not exposed to the breaking change will
   download the the newest release with the reverted changes.
 - users who were exposed to the breaking change can update to
   the latest release and get the old working code again.

Remember that the goal is to always make things easy for users
who depend on a package. If there is any issue whatsoever, all
they should have to do is `pip install --update`. If this
doesn't work, they may have to temporarily pin to a known good
version of a dependency, at least until a fixed release is
uploaded.

After this immediate fire has been put out, if the maintainer
considers the breaking change worth keeping, they can **create a
new package**, with a new namespace. This package will perhaps
have 99% overlap to the previous one and the old one may
eventually be abandoned.

```
mypkg  v201812.0665      # last stable release
mypkg  v201812.0666-rc   # pre release for testers
mypkg  v201901.0667      # final release after testing period

# bug is discovered in v201812.0666-beta and v201901.0667

mypkg  v201901.0668      # identical code to v201812.0665

# new package is created with compatibility breaking code

mypkg2 v201901.0669      # identical code to v201901.0667
mypkg  v201901.0669      # updated readme, declaring support
                         # level for mypkg, pointing to mypgk2
                         # and documenting how to migrate.
```

If this seems like overkill, consider investing time to minimize
the overhead of creating new packages. Consider also that your
projects may recursively depend on dozens of libraries which
you've never even heard of. If every maintainer introduced
breaking changes only once per year, users who depend on these
libraries would be dealing with packaging issues every month! In
other words: *Breaking things is a big deal*. A bit of extra
effort for a few maintainers seems like a fair trade compared to
the effort of many users who would be perfectly happy to use the
old code until they can find the time to migrate.

When creating a new package, it may be worthwhile to rename not
just the package, but also its python module(s). The benefit of
this is that users can install both packages in the same
environment and import both old and new modules. The downside is
that users have to change their code, even if the breaking
change did not affect them.


### Zeno's 1.0 and the Eternal Beta

With PyCalVer, the release tag (`-alpha`, `-beta`, `-rc`) says
something about the stability of a *particular release*. This is
similar ([perhaps identical][pep_101_ref]) to the meaning of
release tags used by the CPython interpreter. A release tag is
not a statement general stability of the software as a whole, it
is metadata about a particular release artifact of a package,
eg. a `.whl` file.

There is a temptation for maintainers to avoid any commitment to
backward compatibility by forever staying in beta or in the case
of SemVer, by never incriminating the major version, leading to
the [Zeno 1.0 paradox][zeno_1_dot_0_ref]. Of course an unpaid
Open Source developer *does not owe anybody a commitment to
backward compatibility*. Especially when a project is young and
going through major changes, such a commitment may not make any
sense. For these cases you can still use PyCalVer, just so long
as there is a big fat warning at the top of your README. Another
way to signify that a project is still in early development is
to not publish a `final` release until the codebase has become
stable.


### Version String Format

The format for PyCalVer version strings can be parsed with this
regular expression:

```python
import re

# https://regex101.com/r/fnj60p/10
PYCALVER_PATTERN = r"""
\b
(?P<version>
    (?P<calver>
       v                        # "v" version prefix
       (?P<year>\d{4})
       (?P<month>\d{2})
    )
    (?P<build>
        \.                      # "." build nr prefix
        \d{4,}
    )
    (?P<release>
        \-                      # "-" release prefix
        (?:alpha|beta|dev|rc|post)
    )?
)(?:\s|$)
"""
PYCALVER_RE = re.compile(PYCALVER_PATTERN, flags=re.VERBOSE)

version_str = "v201712.0001-alpha"
version_info = PYCALVER_RE.match(version_str).groupdict()

assert version_info == {
    "version" : "v201712.0001-alpha",
    "calver"  : "v201712",
    "year"    : "2017",
    "month"   : "12",
    "build"   : ".0001",
    "release" : "-alpha",
}

version_str = "v201712.0033"
version_info = PYCALVER_RE.match(version_str).groupdict()

assert version_info == {
    "version" : "v201712.0033",
    "calver"  : "v201712",
    "year"    : "2017",
    "month"   : "12",
    "build"   : ".0033",
    "release" : None,
}
```

### Incrementing Behaviour

To see how version strings are incremented, we can use
`pycalver test`:

```shell
$ pip install pycalver
...
Successfully installed pycalver-201812.17
$ pycavler --version
pycalver, version v201812.0017
$ pycalver test v201801.0033-beta
PyCalVer Version: v201809.0034-beta
PEP440 Version  : 201809.34b0
```

This is the simple case:

 - The calendar component is updated to the current year and
   month.
 - The build number is incremented by 1.
 - The optional release tag is preserved as is.

You can explicitly update the release tag using the
`--release=<tag>` argument:

```shell
$ pycalver test v201801.0033-alpha --release=beta
PyCalVer Version: v201809.0034-beta
PEP440 Version  : 201809.34b0
$ pycalver test v201809.0034-beta --release=final
PyCalVer Version: v201809.0035
PEP440 Version  : 201809.35
```

To maintain lexical ordering of version numbers, the version
number is padded with extra zeros (see [Lexical
Ids](#lexical-ids) ).


## Usage

### Configuration

The fastest way to setup a project is to use `pycalver init`.


```shell
$ cd my-project
~/my-project$ pycalver init
Updated setup.cfg
```

This will add the something like the following to your
`setup.cfg` (depending on what files you have in your project):

```ini
[pycalver]
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

This probably won't cover all instances of version numbers across
your repository. Something like the following may illustrate
additional changes you might need to make.

```ini
[pycalver]
current_version = v201809.0001-beta
commit = True
tag = True
push = True

[pycalver:file_patterns]
setup.cfg =
    current_version = {version}
setup.py =
    version="{pep440_version}"
myproject/__init__.py =
    __version__ = "{version}"
README.md =
    [PyCalVer {calver}{build}{release}]
    img.shields.io/badge/PyCalVer-{calver}{build}-{release}-blue
```


To see if a pattern is found, you can use the `--dry` flag, which
will leave your repository untouched and only show you a diff.


```shell
$ pycalver bump --dry --no-fetch --release rc
INFO    - Old Version: v201809.0001-beta
INFO    - New Version: v201809.0002-rc
--- README.md
+++ README.md
@@ -11,7 +11,7 @@

 [![Supported Python Versions][pyversions_img]][pyversions_ref]
-[![PyCalVer v201812.0017][version_img]][version_ref]
+[![PyCalVer v201812.0017][version_img]][version_ref]
 [![PyPI Releases][pypi_img]][pypi_ref]

--- myprojcet/__init__.py
+++ myprojcet/__init__.py
@@ -1,1 +1,1 @@
-__version__ = "v201809.0001-beta"
+__version__ = "v201809.0002-rc"

--- setup.py
+++ setup.py
@@ -44,7 +44,7 @@
     name="myproject",
-    version="201812.11b0",
+    version="201812.12rc0",
     license="MIT",
```


### Pattern Search and Replacement

The `pycalver:file_patterns` section of the configuration is
used both to search and also to replace version strings in your
projects files. The following placeholders are available for
use, everything else in a pattern is treated as literal text.


|   placeholder      |      example       |
|--------------------|--------------------|
| `{pep440_version}` | 201809.1b0         |
| `{version}`        | v201809.0001-alpha |
| `{calver}`         | v201809            |
| `{year}`           | 2018               |
| `{month}`          | 09                 |
| `{build}`          | .0001              |
| `{build_no}`       | 0001               |
| `{release}`        | -alpha             |
| `{release_tag}`    | alpha              |


Note that the separator/prefix characters can be part of what is
matched and generated for a given placeholder. In other words,
assuming you have the following text in your README.md (note the
two dashes before alpha):

```
https://img.shields.io/badge/PyCalVer-v201812.0016-None-blue.svg
```

An appropriate pattern would be:

```ini
README.md =
    /badge/PyCalVer {calver}{build}-{release}-blue.svg
```

Notice that neither the "v" prefix, nor the "." and "-"
separators are included in the pattern text, as they are
respectively part of the `calver`, `build` and `release`
placeholders. Alternatively you can be more explicit.

```ini
README.md =
    /badge/PyCalVer v{year}{month}.{build_no}--{release_tag}-blue.svg
```

One limitation to keep in mind is that a version string cannot
span multiple lines.


### Bump It Up

The current version that will be bumped is defined either as

 - Initially: The value of `pycalver.current_version` in
   `setup.cfg`/`pyproject.toml`/`pycalver.toml`. This is only
   used if a project does not use a supported VCS or if no
   version tags have been set so far.
 - Typically: The lexically largest git/mercurial tag in the
   repository.

As part of doing `pycalver bump`, your local VCS index is updated
using `git fetch --tags`/`hg pull`. This ensures that all tags
are known locally and the same version is not generated for
different commits, and mitigates the risk of a rare corner case,
where `p`pycalver bump` is invoked on different machines. If you're
the only maintainer, you can always use `-n/--no-fetch`.


```shell
$ pycalver show --verbose
INFO    - fetching tags from remote (to turn off use: -n / --no-fetch)
Current Version: v201812.0005-beta
PEP440 Version : 201812.5b0
```


To increment and publish a new version, you can use the
`pycalver bump` command, which will do a few things:

 0. Check that your repo doesn't have any local changes.
 1. *Fetch* the most recent global VCS tags from origin
    (--no-fetch to disable).
 2. Generate a new version, incremented from on the most recent
    tag on any branch.
 3. Update version strings in all configured files.
 4. *Commit* the updated version strings.
 5. *Tag* the new commit.
 6. *Push* the new commit and tag.

Again, you can inspect the changes first.

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


### Lexical Ids

The build number padding may eventually be exhausted. In order
to preserve lexical ordering, build numbers are incremented in a
special way. Examples will perhaps illustrate more clearly.

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

What is happening here is that the left-most digit is
incremented early/preemptively. Whenever the left-most digit
would change, the padding of the id is expanded using this
simple formula:

```python
prev_id = "0999"
next_id = str(int(prev_id, 10) + 1)           # "1000"
if prev_id[0] != next_id[0]:                  # "0" != "1"
    next_id = str(int(next_id, 10) * 11)      # 1000 * 11 = 11000
```

This behaviour ensures that the following semantic is always
preserved: `new_version > old_version`. This will always be the
case, even if the padding was expanded and the version number
was incremented multiple times in the same month. To illustrate
the issue, consider what would happen if we did not expand the
padding and instead just incremented numerically.

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

Here we eventually run into a build number where the lexical
ordering is not preserved, since `"10000" < "9999"` (because the
string `"1"` is lexically smaller than `"9"`). This is a very
rare corner case, but it's better to not have to think about it.

Just as an example of why lexical ordering is a nice property to
have, there are lots of software which read git tags, but which
have no logic to parse version strings, which can nonetheless
order the version tags correctly.



[repo_ref]: https://gitlab.com/mbarkhau/pycalver

[setuptools_ref]: https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version

[ssot_ref]: https://en.wikipedia.org/wiki/Single_source_of_truth

[pep_440_ref]: https://www.python.org/dev/peps/pep-0440/

[zeno_1_dot_0_ref]: http://sedimental.org/designing_a_version.html#semver-and-release-blockage

[pep_101_ref]: https://www.python.org/dev/peps/pep-0101/

[bumpversion_ref]: https://github.com/peritus/bumpversion


[build_img]: https://gitlab.com/mbarkhau/pycalver/badges/master/pipeline.svg
[build_ref]: https://gitlab.com/mbarkhau/pycalver/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/pycalver/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/pycalver/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/pycalver/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: http://mypy-lang.org/

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[downloads_img]: https://pepy.tech/badge/pycalver/month
[downloads_ref]: https://pepy.tech/project/pycalver

[version_img]: https://img.shields.io/badge/PyCalVer-v201812.0017-blue.svg
[version_ref]: https://pypi.org/project/pycalver/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/pycalver/#files

[pyversions_img]: https://img.shields.io/pypi/pyversions/pycalver.svg
[pyversions_ref]: https://pypi.python.org/pypi/pycalver

