# Changelog for https://github.com/mbarkhau/bumpver

## BumpVer 2024.1130

This update adds the vendored module `setuptools_v65_version.py` from `setuptools==v65.7.0`.
This was the last version with support for `LegacyVersion`.

- Fix [#242][gh_i242]: Fix incorrect parsing of versions with tags.
- Fix [#156][gh_i156]: Remove runtime dependency on setuptools and looseversion.

[gh_i242]: https://github.com/mbarkhau/bumpver/issues/242
[gh_i156]: https://github.com/mbarkhau/bumpver/issues/156

Thank you [Andrew Mitchell](https://github.com/MitchellAcoustics) and [Tzu-Ting](https://github.com/tzing) for your issue reports.


## BumpVer 2023.1129

- Fix [#224][gh_i224]: Add `--environ` so it emits `0` values. Depricate `-e/--env`.
- Add [#223][gh_pr223]: Add support for `.bumpver.toml`

[gh_i224]: https://github.com/mbarkhau/bumpver/issues/224
[gh_pr223]: https://github.com/mbarkhau/bumpver/pull/223

Thank you [Adrianne](https://github.com/elfgirl) for this issue report.
Thank you [Xavier Francisco](https://github.com/XF-FW) for your contribution.


## BumpVer 2023.1127

- Add [#222][gh_pr222]: Add part HEXHASH.

[gh_pr222]: https://github.com/mbarkhau/bumpver/pull/222

Thank you [Atwam](https://github.com/atwam) for your contribution.


## BumpVer 2023.1126

- Add [#214][gh_pr214]: Support for pre/post commit hooks.
- Add [#219][gh_pr219]: Fix pathlib issues on Windows.
- Fix [#201][gh_i201]: Better error message for SemVer corner case.
- Update [#215][gh_i215]: Better error message for greedy pattern matching.
- Update [#216][gh_i216]: Use .toml format in REAMDE examples.

[gh_pr214]: https://github.com/mbarkhau/bumpver/pull/214
[gh_pr219]: https://github.com/mbarkhau/bumpver/pull/219
[gh_i201]: https://github.com/mbarkhau/bumpver/issues/201
[gh_i215]: https://github.com/mbarkhau/bumpver/issues/215
[gh_i216]: https://github.com/mbarkhau/bumpver/issues/216

Thank you [Sven Lohrmann](https://github.com/malnvenshorn) for your contribution.
Thank you [Maikel Punie](https://github.com/Cereal2nd) your issue report.
Thank you for your help in debugging Windows issues:
 - [Søren Furbo](https://github.com/SRFU-NN)
 - [Michal Vašut](https://github.com/MichalVasut)
 - [Justin Cooksey](https://github.com/jscooksey)
 - [yqbear](https://github.com/yqbear)


## BumpVer 2023.1125

- Add [#188][gh_i188]: Add `--tag-scope=<SCOPE>` to support separate versioning for branches.
- Add [#185][gh_i185]: Add `--tag-message=<TMPL>` parameter and `tag_message` configuration option.
- Fix [#209][gh_i209]: Make `--no-tag-commit` ommit `--follow-tags`.

[gh_i188]: https://github.com/mbarkhau/bumpver/issues/188
[gh_i185]: https://github.com/mbarkhau/bumpver/issues/185
[gh_i209]: https://github.com/mbarkhau/bumpver/issues/209

Thank you [Sven Lohrmann](https://github.com/malnvenshorn) for your contributions.
Thank you [tardis4500](https://github.com/tardis4500) for the issue report.


## BumpVer 2023.1124

- Fix [#208][gh_i208]: Fix handling of versions with PEP440 epoch.

[gh_i208]: https://github.com/mbarkhau/bumpver/issues/208

Thank you [Wen Kokke](https://github.com/wenkokke) for the issue report.


## BumpVer 2023.1122

- Fix [#207][gh_i207]: Add --ignore-vcs-tag to support bumping older versions

[gh_i207]: https://github.com/mbarkhau/bumpver/issues/207

Thank you [Jusong Yu](https://github.com/unkcpz) for your contribution.


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
