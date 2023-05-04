# Changelog for https://github.com/mbarkhau/bumpver

## BumpVer 2023.1121

- Fix [#200][gh_i200]: Fix compatability with packaging 23.0.
- Fix [#203][gh_i203]: Add dev to the list of valid release tags

[gh_i200]: https://github.com/mbarkhau/bumpver/issues/200
[gh_i203]: https://github.com/mbarkhau/bumpver/issues/203

Thank you [Sharon Yogev](https://github.com/sharonyogev) for your contribution.


## BumpVer 2022.1120

- Fix [#196][gh_i196]: Add `--pin-increments`.

[gh_i196]: https://github.com/mbarkhau/bumpver/issues/196

Thank you [Markus Holtermann](https://github.com/MarkusH) for
this contribution.


## BumpVer 2022.1119

- Fix [#190][gh_i190]: Allow multiple patterns on the same line

- Fix [#182][gh_i182]: Use quotes for vcs commands

[gh_i190]: https://github.com/mbarkhau/bumpver/issues/190
[gh_i182]: https://github.com/mbarkhau/bumpver/issues/182


## BumpVer 2022.1118

- Fix [#181][gh_i181]: Enable use of ``^$`` charachters to restrict
  matching to beginning and end of line.
- Add ``GITHASH`` to ``version_pattern`` (@mpasternak)

[gh_i181]: https://github.com/mbarkhau/bumpver/issues/181


## BumpVer 2022.1116

 - Fix: [incorrect version comparison when updating from vcs tag][gh_i174].

   When comparing the updated version to the latest vcs tag,
   an insufficient string comparison was used instead of
   comparing the parsed versions.

[gh_i174]: https://github.com/mbarkhau/bumpver/issues/174

Thank you to Timo Ludwig @timoludwig for this contribution.


## BumpVer 2022.1115

 - Fix: [use default date values][gh_i172].

   When parsing the current version, if it doesn't specify anyt
   date part, (such as is the case for e.g. SemVer), then use the
   current date to populate default parts.

   This enables updating YYYY patterns in copyright headers even
   for projects that don't use a CalVer pattern.

   Thank you [Benjamin Depardon (@bdepardo)][gh_bdepardo] for
   finding and reporting this issue.

[gh_i172]: https://github.com/mbarkhau/bumpver/issues/172
[gh_bdepardo]: https://github.com/bdepardo


## BumpVer 2021.1114

 - Add: [flags to override vcs options][gh_i168] for `bumpver update`

[gh_i168]: https://github.com/mbarkhau/bumpver/issues/168

Thank you to Timo Ludwig @timoludwig for this contribution.


## BumpVer 2021.1113

 - Add: [`--commit-message` argument][gh_i162] for `bumpver update`

[gh_i162]: https://github.com/mbarkhau/bumpver/issues/162


## BumpVer 2021.1112

 - Fix: Build from source on windows.


## BumpVer 2021.1110

 - Fix [github#157][gh_i157]: Improve error messages.
 - Fix [github#158][gh_i158]: Clarify `PYTAGNUM` "part"

[gh_i157]: https://github.com/mbarkhau/bumpver/issues/157
[gh_i158]: https://github.com/mbarkhau/bumpver/issues/158

Thank you to Julien Palard @JulienPalard for testing and feedback.


## BumpVer 2021.1109

 - Add `-e/--env` option to support shell script automation.
 - Fix [github#151][gh_i151]: invalid increment of `TAGNUM` when `TAG=final` is set.

[gh_i151]: https://github.com/mbarkhau/bumpver/issues/151

Thank you to Dave Wapstra @dwapstra for your contributions.


## BumpVer 2020.1108

- Don't match empty patterns (possibly causing a whole file to be rewritten if braces `[]` are not escaped).


## BumpVer 2020.1107

- Non-Beta release (no significant code changes).

## BumpVer 2020.1105-beta

- Fix [gitlab#15][gitlab_i15]: Fix config parsing corner case.
- Fix [gitlab#16][gitlab_i16]: Fix rollover handling for tag/pytag.

[gitlab_i15]: https://gitlab.com/mbarkhau/pycalver/-/issues/15
[gitlab_i16]: https://gitlab.com/mbarkhau/pycalver/-/issues/16


## BumpVer 2020.1104-beta

- Fix [gitlab#13][gitlab_i13]: Add `--set-version=<VERSION>` to explicitly set version.
- Fix [gitlab#14][gitlab_i14]: Parse `tool.bumpver` when using pyproject.toml as per PEP 518.

[gitlab_i13]: https://gitlab.com/mbarkhau/pycalver/-/issues/13
[gitlab_i14]: https://gitlab.com/mbarkhau/pycalver/-/issues/14


## BumpVer 2020.1100-beta

Rename package and module from PyCalVer to BumpVer. This name change is due to confusion that this project is either Python specific, or only suitible for CalVer versioning schemes, neither of which is the case.

This release includes a new syntax for patterns.

```
version_pattern = "vYYYY0M.BUILD[-RELEASE]"             # new style
version_pattern = "v{year}{month}{build}{release}"      # old style

version_pattern = "MAJOR.MINOR.PATCH"                   # new style semver
version_pattern = "{MAJOR}.{MINOR}.{PATCH}"             # old style semver
```

The main reasons for this switch were:
- To enable optional parts using braces `[PART]`.
- To align the syntax with the conventions used on CalVer.org

The previous syntax will continue to be supported, but all documentation has been updated to primarily reference new style patterns.

- Switch main repo from gitlab to github.
- New [gitlab#7][gitlab_i7]: New style pattern syntax.
  - Better support for week numbers.
  - Better support for optional parts.
  - New: `BUILD` part now starts at `1000` instead of `0001` to avoid truncation of leading zeros.
  - New: Add `INC0` (0-based) and `INC1` (1-based) parts that do auto increment and rollover.
  - New: `MAJOR`/`MINOR`/`PATCH`/`INC` will roll over when a date part changes to their left.
- New [gitlab#2][gitlab_i2]: Added `grep` sub-command to help with debugging of patterns.
- New [gitlab#10][gitlab_i10]: `--pin-date` to keep date parts unchanged, and only increment non-date parts.
- New: Added `--date=<iso-date>` parameter to set explicit date (instead of current date).
- New: Added `--release-num` to increment the `alphaN`/`betaN`/`a0`/`b0`/etc. release number
- New: Added better error messages to debug regular expressions.
- New [gitlab#9][gitlab_i9]: Make commit message configurable.
- Fix [gitlab#12][gitlab_i12]: Error with sorting non-lexical version tags (e.g. SemVer).
- Fix [gitlab#11][gitlab_i11]: Show regexp when `--verbose` is used.
- Fix [gitlab#8][gitlab_i8]: `bumpver update` will now also push HEAD (previously only the tag itself was pushed).
- Fix: Disallow `--release=dev`. The semantics of a `dev` releases are different than for other release tags and further development would be required to support them correctly.
- Fix: Entries in `file_patterns` were ignored if there were multiple entries for the same file.

This release no longer includes the `pycalver.lexid` module, which has been moved into its own package: [pypi.org/project/lexid/](https://pypi.org/project/lexid/).

Many thanks to contributors of this release: @LucidOne, @khanguslee, @chaudum

[gitlab_i7]:https://gitlab.com/mbarkhau/pycalver/-/issues/7
[gitlab_i2]: https://gitlab.com/mbarkhau/pycalver/-/issues/2
[gitlab_i10]: https://gitlab.com/mbarkhau/pycalver/-/issues/10
[gitlab_i9]: https://gitlab.com/mbarkhau/pycalver/-/issues/9
[gitlab_i12]: https://gitlab.com/mbarkhau/pycalver/-/issues/12
[gitlab_i11]: https://gitlab.com/mbarkhau/pycalver/-/issues/11
[gitlab_i8]: https://gitlab.com/mbarkhau/pycalver/-/issues/8


## PyCalVer v202010.1042

- Add deprication warning to README.md


## PyCalVer v201907.0036

- Fix: Don't use git/hg command if `commit=False` is configured (thanks @valentin87)


## PyCalVer v201907.0035

- Fix [gitlab#6][gitlab_i6]: Add parts `{month_short}`, `{dom_short}`, `{doy_short}`.
- Fix [gitlab#5][gitlab_i5]: Better warning when using bump with SemVer (one of --major/--minor/--patch is required)
- Fix [gitlab#4][gitlab_i4]: Make {release} part optional, so that versions generated by --release=final are parsed.

[gitlab_i6]: https://gitlab.com/mbarkhau/pycalver/-/issues/6
[gitlab_i5]: https://gitlab.com/mbarkhau/pycalver/-/issues/5
[gitlab_i4]: https://gitlab.com/mbarkhau/pycalver/-/issues/4


## PyCalVer v201903.0030

- Fix: Use pattern from config instead of hard-coded {pycalver} pattern.
- Fix: Better error messages for git/hg issues.
- Add: Implicit default pattern for config file.


## PyCalVer v201903.0028

- Fix: Add warnings when configured files are not under version control.
- Add: Colored output for bump --dry


## PyCalVer v201902.0027

- Fix: Allow --release=post
- Fix: Better error reporting for bad patterns
- Fix: Regex escaping issue with "?"


## PyCalVer v201902.0024

- Added: Support for globs in file patterns.
- Fixed: Better error reporting for invalid config.


## PyCalVer v201902.0020

- Added: Support for many more custom version patterns.


## PyCalVer v201812.0018

- Fixed: Better handling of pattern replacements with "-final" releases.


## PyCalVer v201812.0017

- Fixed [github#2]. `pycalver init` was broken.
- Fixed pattern escaping issues.
- Added lots more tests for cli.
- Cleaned up documentation.

[gihlab_i2]: https://github.com/mbarkhau/pycalver/-/issues/2


## PyCalVer v201812.0011-beta

- Add version tags using git/hg.
- Use git/hg tags as SSOT for most recent version.
- Start using https://gitlab.com/mbarkhau/bootstrapit
- Move to https://gitlab.com/mbarkhau/pycalver


## PyCalVer v201809.0001-alpha

- Initial release
