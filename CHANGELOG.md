# Changelog for https://gitlab.com/mbarkhau/pycalver


## v201903.0028

 - Fix: Add warnings when configured files are not under version control.
 - Add: Coloured output for bump --dry


## v201902.0027

 - Fix: Allow --release=post
 - Fix: Better error reporting for bad patterns
 - Fix: Regex escaping issue with "?"
 

## v201902.0024

 - Added: Support for globs in file patterns.
 - Fixed: Better error reporting for invalid config.
 

## v201902.0020

 - Added: Support for many more custom version patterns.


## v201812.0018

 - Fixed: Better handling of pattern replacements with "-final" releases.


## v201812.0017

 - Fixed #2 on github. `pycalver init` was broken.
 - Fixed pattern escaping issues.
 - Added lots more tests for cli.
 - Cleaned up documentation.


## v201812.0011-beta

 - Add version tags using git/hg.
 - Use git/hg tags as SSOT for most recent version.
 - Start using https://gitlab.com/mbarkhau/bootstrapit
 - Move to https://gitlab.com/mbarkhau/pycalver


## v201809.0001-alpha

 - Initial release
