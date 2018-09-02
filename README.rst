PyCalVer: Automatic CalVer Versioning for Python Packages
=========================================================

PyCalVer is a very simple versioning system,
which is compatible with python packaging software
(
`setuptools <https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version>`_,
`PEP440 <https://www.python.org/dev/peps/pep-0440/>`_
).

.. start-badges

.. list-table::
    :stub-columns: 1

    * - package
      - | |license| |wheel| |pyversions| |pypi| |version|
    * - tests
      - | |travis| |mypy| |coverage|

.. |travis| image:: https://api.travis-ci.org/mbarkhau/pycalver.svg?branch=master
    :target: https://travis-ci.org/mbarkhau/pycalver
    :alt: Build Status

.. |mypy| image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: http://mypy-lang.org/
    :alt: Checked with mypy

.. |coverage| image:: https://img.shields.io/badge/coverage-86%25-green.svg
    :target: https://travis-ci.org/mbarkhau/pycalver
    :alt: Code Coverage

.. |license| image:: https://img.shields.io/pypi/l/pycalver.svg
    :target: https://github.com/mbarkhau/pycalver/blob/master/LICENSE
    :alt: MIT License

.. |pypi| image:: https://img.shields.io/pypi/v/pycalver.svg
    :target: https://pypi.python.org/pypi/pycalver
    :alt: PyPI Version

.. |version| image:: https://img.shields.io/badge/CalVer-v201809.0002--beta-blue.svg
    :target: https://calver.org/
    :alt: CalVer v201809.0002-beta

.. |wheel| image:: https://img.shields.io/pypi/wheel/pycalver.svg
    :target: https://pypi.org/project/pycalver/#files
    :alt: PyPI Wheel

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/pycalver.svg
    :target: https://pypi.python.org/pypi/pycalver
    :alt: Supported Python Versions


The PyCalVer package provides the ``pycalver`` command and
module to generate version strings which follow the format:
``v{calendar_version}.{build_number}[-{release_tag}]``

Some examples:


.. code-block::

    v201711.0001-alpha
    v201712.0027-beta
    v201801.0031
    v201801.0032-post
    ...
    v202207.18133
    v202207.18134


The ``pycalver bump`` command will parse specified/configured
files for such strings and rewrite them with an updated version
string.

The format accepted by PyCalVer can be parsed with this regular
expression:


.. code-block:: python

    import re

    # https://regex101.com/r/fnj60p/10
    pycalver_re = re.compile(r"""
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
    """, flags=re.VERBOSE)

    version_str = "v201712.0001-alpha"
    version_info = pycalver_re.match(version_str).groupdict()

    assert version_info == {
        "version" : "v201712.0001-alpha",
        "calver"  : "v201712",
        "year"    : "2017",
        "month"   : "12",
        "build"   : ".0001",
        "release" : "-alpha",
    }

    version_str = "v201712.0033"
    version_info = pycalver_re.match(version_str).groupdict()

    assert version_info == {
        "version" : "v201712.0033",
        "calver"  : "v201712",
        "year"    : "2017",
        "month"   : "12",
        "build"   : ".0033",
        "release" : None,
    }


Installation
------------

Before we look at project setup, we can simply install and test
by passing a version string to ``pycalver incr``.


.. code-block:: bash

    $ pip install pycalver

    $ pycalver incr v201801.0033-beta
    PyCalVer Version: v201809.0034-beta
    PEP440 Version: 201809.34b0

    $ pycalver incr v201801.0033-beta --release=final
    PyCalVer Version: v201809.0034
    PEP440 Version: 201809.34

    $ pycalver incr v201809.1999
    PyCalVer Version: v201809.22000
    PEP440 Version: 201809.22000


The CalVer component is set to the current year and month, the
build number is incremented by one and the optional release tag
is preserved as is, unless specified otherwise via the
``--release=<tag>`` parameter.


Configuration
-------------

The fastest way to setup a project is to invoke
``pycalver init``.


.. code-block:: bash

    $ cd my-project
    ~/my-project$ pycalver init
    Updated setup.cfg


.. code-block:: ini

    # setup.cfg
    [bdist_wheel]
    universal = 1

    [pycalver]
    current_version = v201809.0001-dev
    commit = True
    tag = True

    [pycalver:file:setup.cfg]
    patterns =
        current_version = {version}

    [pycalver:file:setup.py]
    patterns =
        "{version}",
        "{pep440_version}",

    [pycalver:file:README.rst]
    patterns =
        {version}
        {pep440_version}


Depending on your project, the above will probably cover all
version numbers across your repository. Something like the
following may illustrate additional changes you'll need to make.


.. code-block:: ini

    # setup.cfg
    [pycalver]
    current_version = v201809.0001-beta
    commit = True
    tag = True

    [pycalver:file:setup.cfg]
    patterns =
        current_version = {version}

    [pycalver:file:setup.py]
    patterns =
        version="{pep440_version}"

    [pycalver:file:src/myproject.py]
    patterns =
        __version__ = "{version}"

    [pycalver:file:README.rst]
    patterns =
        badge/CalVer-{calver}{build}-{release}-blue.svg
        :alt: CalVer {version}


If ``patterns`` is not specified for a ``pycalver:file:``
section, the default patterns are used:


.. code-block:: ini

    [pycalver:file:src/myproject.py]
    patterns =
        {version}
        {pep440_version}


This allows us to less explicit but shorter configuration, like
this:


.. code-block:: ini

    [pycalver]
    current_version = v201809.0001-beta
    commit = True
    tag = True

    [pycalver:file:setup.cfg]
    [pycalver:file:setup.py]
    [pycalver:file:src/myproject.py]
    [pycalver:file:README.rst]
    patterns =
        badge/CalVer-{calver}{build}-{release}-blue.svg
        :alt: CalVer {version}


Pattern Search and Replacement
------------------------------

``patterns`` is used both to search for version strings and to
generate the replacement strings. The following placeholders are
available for use, everything else in a pattern is treated as
literal text.

.. table:: Patterns Placeholders

    ================== ======================
    placeholder        example
    ================== ======================
    ``pep440_version`` 201809.1b0
    ``version``        v201809.0001-alpha
    ``calver``         v201809
    ``year``           2018
    ``month``          09
    ``build``          .0001
    ``release``        -alpha
    ================== ======================

Note that the separator/prefix characters are part of what is
matched and generated for a given placeholder, and they should
not be included in your patterns.

A further restriction is, that a version string cannot span
multiple lines in your source file.


Pattern Search and Replacement
------------------------------

Now we can call ``pycalver bump`` to bump all occurrences of
version strings in these files. Normally this will change local
files, but the ``--dry`` flag will instead display a diff of the
changes that would be applied.


.. code-block:: bash

    $ pycalver show
    Current Version: v201809.0001-beta
    PEP440 Version: 201809.1b0

    $ pycalver bump --dry
    TODO
    Don't forget to git push --tags



Other Versioning Software
-------------------------

This project is very similar to bumpversion, upon which it is
partially based, but since the PyCalVer version strings can be
generated automatically, usage is quite a bit more simple. Users
do not have to deal with parsing and generating version strings.
Most of the interaction that users will have is reduced to two
commands:


.. code-block:: bash

    $ pycalver bump
    TODO: Output


More rarely, when changing the release type:

.. code-block:: bash

    $ pycalver bump --release beta
    TODO: Output

    $ pycalver bump --release final
    TODO: Output


Some Details
------------

 - Version numbers are for public releases. For the purposes of
   development of the project itself, reference VCS branches and
   commit ids are more appropriate.
 - There should be only one person or system responsible for
   updating the version number at the time of release, otherwise
   the same version number may be generated for different builds.
 - Lexeographical order is


Canonical PyCalVer version strings can be parsed with this
regular expression:


These are the full version strings, for public announcements and
conversations it will often be sufficient to refer simply to
``v201801``, by which the most recent ``post`` release build of
that month is meant.



    version_str = "v201712.0027-beta"
    version_dict = pycalver_re.match("v201712.0027-beta").groupdict()
    import pkg_resources    # from setuptools
    version = pkg_resources.parse_version(version_str)
    --

    In [2]: version_dict
    {'year': '2017', 'month': '12', 'build_nr': '0027', 'tag': 'beta'}
    >>> str(version)
    201712.27b0


Lexical Ids
-----------

Most projects will be served perfectly well by the default four
digit zero padded build number. Depending on your build system
however, you may get into higher build numbers. Since build
numbers have no semantic meaning (beyond larger = later/newer),
they are incremented in a way that preserves lexical ordering as
well as numerical order. Examples will perhaps illustrate more
clearly.

.. code-block:: python

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

What is happening here is that the left-most digit is incremented
early, whenever the left-most digit changes. The formula is very simple:

.. code-block:: python

    prev_id = "0999"
    next_id = str(int(prev_id, 10) + 1)           # "1000"
    if prev_id[0] != next_id[0]:                  # "0" != "1"
        next_id = str(int(next_id, 10) * 11)      # 1000 * 11 = 11000


In practice you can just ignore the left-most digit, in case you
do want to read something into the semantically meaningless
build number.


Realities of Verion Numbers
---------------------------

Nobody knows what the semantics of a version number are, because
nobody can guarantee that a given release adheres to whatever
convention one would like to imbibe it with. Lets just keep things
simple.

 - Version numbers should be recognizable as such, that's what
   the "v" prefix does.
 - A number like 201808 is recognizable to many as a number
   derived from a calendar.
 - alpha, beta are common parlance indicating software which is
   still under development.

Some additional constraints are applied to conform with PEP440


Should I use PyCalVer for my Project?
-------------------------------------

If your project is 1. not useful by itself, but only when used
by other software, 2. has a finite scope/a definition of "done",
3. your project has CI, a test suite with and decent code
coverage, then PyCalVer is worth considering.
You release at most once per month.


Marketing/Vanity
----------------

Quotes from http://sedimental.org/designing_a_version.html


Rational
--------

PyCalVer is opinionated software. This keeps things simple,
when the opintions match yours, but makes it useless for
everybody else.

The less machine parsable semantics you put in your version
string, the better. The ideal would be to only have a single
semantic: newer == better.

Some projects depend recursively on hundreds of libraries, so
compatability issues generated by your project can be a heavy
burdon on thousands of users; users who learn of the existance
of your library for the first time in the form of a stacktrace.
PyCalVer is for projects that are comitted to and can maintain
backward compatability. Newer versions are always better,
updates are always safe, an update won't break things, and if it
does, the maintainer's hair is on fire and they will publish a
new release containing a fix ASAP.

Ideally, your user can just declare your library as a
dependency, without any extra version qualifier, and never have
to think about it again. If you do break something by accident,
their remedy is not to change their code, but to temporarily pin
an earlier version, until your bugfix release is ready.

PyCalVer is for projects which are the mundane but dependable
foundations of other big shiny projects, which get to do their
big and exciting 2.0 major releases.


Breaking Things is a Big Deal
-----------------------------

Using an increment in a version string to express that a release
may break client code is not tennable. A developer cannot be
expected to think about how their code may or may not break as a
consequence of your decision to rename some functions. As the
author of any software, there is a great temptation to move fast
and break things. This is great when no other software depends
on yours. If something breaks, you jump up and fix it. The story
is quite different even when only a few dozen people depend on
your software.


The less the users of your library have to know about your
project, the better. The less they have to deal with issues
of compatability, the better. SemVer can be overly specifc
for some kinds of projects. If you are writing a library
and you have a commitment to backward compatability

PyCalVer version strings can be parsed according to PEP440
https://www.python.org/dev/peps/pep-0440/


A Word on Marketing
-------------------

This setup of expectations for users can go one of two ways,

We use version numbers to communicate between the authors
of software and its users. For users of libraries Particularly
for libraries, it pays to keep things as simple as possible for
your human users.


Commitment to Compatability
---------------------------

Software projects can depend on many libraries. Consider that one
package introducing a breaking change is enough to mess up your
day. Especially in the case of libraries, your users should be
able to write code that uses it and not have that code break at
any point in the future. Users cannot be asked to keep track of
all the changes to every little library that they use.

PyCalVer is explicitly non semantic. A PyCalVer version number does
not express anything about

    - Don't ever break things. When users depend on your
      software, backward compatability matters and the way to
      express backward incompatible changes is not to bump a
      version number, but to change the package name. A change
      in the package name clearly communicates that a user must
      change their code so that it will work with the changed
      API. Everybody who does not have the bandwith for those
      changes, doesn't even have to be aware of your new
      release.

    - When you do break something, that should be considered a
      bug that has to be fixed as quickly as possible in a new
      version. It should always be safe for a user to update
      their dependencies. If something does break, users have to
      temporarilly pin an older (known good) version, or update
      to a newer fixed version.

    - Version numbers should not require a parser (present
      package excluded of course). A newer version number should
      always be lexeographically greater than an older one.
      TODO:
      https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version


The main component of the version number is based on the
calendar date. This is allows you to show your commitment (or
lack thereof) to the maintenance of your libarary. It also
allows users to see at a glance that their dependency might be
out of date. In this versioning scheme it is completely
reasonable to bump the version number without any changes,
simply to express to your users, that you are still actively
maintaining the software and that it is in a known good state.


For a much more detailed exposition of CalVer, see
http://sedimental.org/designing_a_version.html
https://calver.org/

from pkg_resources import parse_version


The Life of a Library
---------------------

mylib      v201711.001-alpha     # birth of a project (in alpha)
mylib      v201711.002-alpha     # new features (in alpha)
mylib      v201712.003-beta      # bugfix release (in beta)
mylib      v201712.004-rc        # release candidate
mylib      v201712.005           # stable release
mylib      v201712.006           # stable bugfix release

mylib2     v201712.007-beta      # breaking change (new package name!)
mylib2     v201801.008-beta      # new features (in beta)
mylib2     v201801.009           # stable release

mylib      v201802.007           # security fix for legacy version
mylib2     v201802.010           # security fix

mylib2     v202604.9900           # threshold for four digit build numbers
mylib2     v202604.9901           # still four digits in the same month
mylib2     v202604.9911           # last build number with four digits
mylib2     v202605.09912          # build number zero padding added with date turnover
mylib2     v202605.09913          # stable release

mylib2     v203202.16051-rc       # release candidate
mylib2     v203202.16052          # stable release

    ...
    v202008.500    # 500 is the limit for four digit build numbers, but
    v202008.508    # zero padding is added only after the turnover to
    v202009.0509   # a new month, so that lexical ordering is preserved.

The date portion of the version, gives the user an indication of
how up their dependency is, whether or not a project is still
being maintained.

The build number, gives the user an idea of the maturity of the
project. A project which has been around long enough to produce
hundreds of builds, might be considered mature, or at least a
project that is only on build number 10, is probably still in
early development.


FAQ
---

Q: "So you're trying to tell me I need to create a whole new
package every time I introduce a introduce a breaking change?!".

A: First of all, what the hell are you doing? Secondly, YES!
Let's assume your little package has even just 100 users. Do you
have any idea about the total effort that will be expended
because you decided it would be nice to change the name of a
function? It is completely reasonable introduce that the
friction for the package author when the price to users is
orders of magnitude larger.


1801

https://calver.org/

I have given up on the idea that version numbers express
anything about changes made between versions. Trying to
express such information assumes 1. that the author of a package
is aware of how a given change needs to be reflected in a
version number and 2. that users and packaging softare correctly
parse that meaning. When I used semantic versioning, I realized that
the major version number of my packages would never change,
because I don't think breaking changes should ever be