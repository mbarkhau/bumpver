# Contributing

<!--
  $ pip install md-toc
  $ md_toc -i gitlab CONTRIBUTING.md.template
-->

[](TOC)

- [Contributing](#contributing)
    - [Introduction](#introduction)
    - [Setup](#setup)
        - [Setup SSH keys](#setup-ssh-keys)
        - [Setup Virtual Environments](#setup-virtual-environments)
    - [Project Types](#project-types)
    - [Project Layout](#project-layout)
        - [Dependency Management](#dependency-management)
- [These are not used on production, or staging, only](#these-are-not-used-on-production-or-staging-only)
- [on development machines and the CI environment.](#on-development-machines-and-the-ci-environment)
- [These are the requirements produced for specific builds. They can be](#these-are-the-requirements-produced-for-specific-builds-they-can-be)
- [used to debug version compatatbility issues . They are generated](#used-to-debug-version-compatatbility-issues-they-are-generated)
- [using pip freeze](#using-pip-freeze)
        - [Vendoring](#vendoring)
    - [Development](#development)
        - [Linting](#linting)
        - [Type Checking](#type-checking)
        - [Documentation](#documentation)
        - [Setup to run docker](#setup-to-run-docker)
        - [PyCharm](#pycharm)
        - [Sublime Text](#sublime-text)
    - [Best Practices](#best-practices)

[](TOC)


## Introduction

Friction for new contributors should be as low as possible. Ideally a
new contributor, starting any unix[^1] system can go through these
steps and not encounter any errors:

 1. `git clone <project_url>`
 2. `cd <project>`
 3. `make install`
 4. `# get some coffee`
 5. `make lint`
 6. `make test`
 7. `make serve`

If you as a new contributor encounter any errors, then please create
an issue report and you will already have made a great contribution!


## Setup

The development workflow described here is documented based on a Unix
environment. Hopefully this will reduce discrepancies between
development and production systems.


### Setup SSH keys

Projects which depend on private repositories require ssh to
connect to remote servers. If this is the case, you should make
sure that your ssh keys are available in `${HOME}/.ssh`, or you
will have to do `ssh-keygen` and install the generated public
key to host system. If this is not done, `pip install` will fail
to install these dependencies from your private repositiories with
an error like this

```shell
Downloading/unpacking git+git://...git
Cloning Git repository git://

Permission denied (publickey).

fatal: The remote end hung up unexpectedly
----------------------------------------
Command /usr/local/bin/git clone ... failed with error code 128
```


### Setup Virtual Environments

The first setup can take a while, since it will install miniconda and
download lots of dependencies for the first time. If you would like to
know more about conda, there is a good article written by Gergely
Szerovay: https://medium.freecodecamp.org/85f155f4353c

```shell
dev@host:~
$ git clone git@../group/project.git
Cloning Git repository git@../group/project.git to project
...

$ cd project

dev@host:~/project
$ make install
Solving environment:
...
```

This will do quite a few things.

1. Install miniconda3, if it isn't already installed. It checks
   the path `$HOME/miniconda3` for an existing installation
2. Creates python virtual environments for all supported python
   versions of this project.
3. Installs application and development dependencies to the
   environments.
4. Installs vendored dependencies into `vendor/`

If installation was successful, you should be able to at least
run the linter (assuming previous developers have a bare minimum
of diligence).

```console
$ make lint
flake8 .. ok
mypy .... ok
doc ..... ok
```

If this is the first time conda has been installed on your
system, you'll probably want to enable the `conda` command:

```
$ echo ". ${HOME}/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
$ conda --version
conda 4.5.11
```

You can also activate the default virtual environment as follows.


```shell
(myproject_py36) dev@host:~/myproject
$ source ./activate
$ which python
/home/dev/miniconda3/envs/myproject_py36/bin/python

$ ipython
Python 3.6.6 |Anaconda, Inc.| (default, Jun 28 2018, 17:14:51)
t Type 'copyright', 'credits' or 'license' for more information
IPython 6.5.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import sys

In [2]: sys.path
Out[2]:
['/home/dev/miniconda3/envs/pycalver_py36/bin',
 '/home/dev/myproject/src',
 '/home/dev/myproject/vendor',
 ...
In [3]: import myproject

In [4]: myproject.__file__
Out[4]: '/home/dev/myproject/src/myproject/__init__.py'
```

Note that the `PYTHONPATH` has been set up to import modules
of the project. You can review the definition for `make ipy`
to see how to set up `PYTHONPATH` correctly.


```shell
$ make ipy --dry-run
ENV=${ENV-dev} PYTHONPATH=src/:vendor/:$PYTHONPATH \
    /home/dev/miniconda3/envs/myproject_py36/bin/ipython
$ make ipy
Python 3.6.6 |Anaconda, Inc.| (default, Jun 28 2018, 17:14:51)
Type 'copyright', 'credits' or 'license' for more information
IPython 6.5.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import myproject

In [2]: myproject.__file__
Out[2]: '/home/dev/myproject/src/myproject/__init__.py'
```


## Project Types

These guidelines written for different kinds of projects, each of
which is ideally: small, focosued and reusable. These projects can be:

 1. Services: Projects which are deployed and run continuously.
 2. Libraries: Projects which are not deployed by themselves but
    installed and used by others.
 3. CLI Tools: Projects which are installed and mainly used by
    developers and admins.

The choices made here are intended to make it easy to start new
projects by reducing the burdon of project setup to a minimum.


## Project Layout

    src/               # source code of project
    vendor/            # vendored dependencies
    stubs/             # mypy .pyi stub files
    test/              # pytest test files (files begin with test_)
    scripts/           # miscalenious scripts used deployment and ops

    requirements/      # dependency metadata files
    docs/              # documentation source files
    data/              # fixtures for unit tests and db initialization

    setup.py           # main python package metadata
    setup.cfg          # misc python tooling configuration

    README.md          # project overview and status
    CONTRIBUTING.md    # guide for developers
    CHANGELOG.md       # short documentation of release history
    LICENSE            # for public libraries (MIT preferred)

    makefile                    # project specific configuration
                                # variables and make targets
    makefile.bootstrapit.make   # bootstrapit make include library

    docker_base.Dockerfile  # base image for CI (only conda envs)
    Dockerfile              # image with source of the project


### Dependency Management


Dependencies are managed using a set of requirements/\*.txt files. You
only need to know about this if you want to add or change a dependency.


```shell
requirements/conda.txt          # installed via conda from main or conda-forge
requirements/pypi.txt           # installed via pip from pypi to virutal environments
requirements/vendor.txt         # installed via pip from pypi to vendor/

# These are not used on production, or staging, only
# on development machines and the CI environment.
requirements/development.txt    # useful packgages for development/debugging
requirements/integration.txt    # used for linting/testing/packaging

# These are the requirements produced for specific builds. They can be
# used to debug version compatatbility issues. They are generated
# using make freeze
requirements/20190214t212403_freeze.txt
```


When adding a new dependency please consider:

- Only specify direct dependencies of the project, not transitive
  dependencies of other projects. These are installed via their
  own respective dependency declarations.
- Whenever possible, the specifier for a package should be only its
  name without a version specifier. With this as the default, the
  project remains   up to date in terms of security fixes and other
  library improvements.
- Some packages consider some of their dependancies to be optional,
  in which case you will have to specify their transitive
  dependencies.
- Only specify/pin/freeze a specific (older) version if there are
  known issues, or your project requires features from an unstable
  (alpha/beta) version of the package. Each pinned version should
  document why it was pinned, so that it can later be determined if
  the issue has been resolved in the meantime.

One argument against this approach is the issue of rogue package
maintainers. A package maintainer might release a new version which
you automatically install using `make update`, and this new code opens
a back door or proceeds to send data from your production system to a
random server on the internet.

The only prodection pypi or conda-forge have against this is to remove
packages that are reported to them. If you are paranoid, you could
start pinning dependencies to older versions, for which you feel
comfortable that any issues would have been noticed. This is only a
half measure however, since the issues may not be noticed even after
months.

Ultimately, if data breaches are a concern you should talk to your
network admin about firewall rules and if data loss is a concern you
should review your backup policy.

Further Reading:
  https://hackernoon.com/building-a-botnet-on-pypi-be1ad280b8d6
  https://python-security.readthedocs.io/packages.html

Dependencies are installed in this order:

 - `conda.txt`
 - `pypi.txt`
 - `vendor.txt`
 - `development.txt`
 - `integration.txt`

Please review the documentation header at the beginning of each
`requirements/*.txt` file to determine which file is appropriate
for the dependency you want to add.

Choose a file:

- `conda.txt` is appropriate for non python packages and packages
  which would require compilation if they were downloaded from pypi
  or cannot be downloaded from pypi (such as openjdk or node).
- `pypi.txt` is for dependencies on python packages, be they from
  pypi or git repositories.
- `vendor.txt` is appropriate for pure python libaries which are
  written using mypy. This allows the mypy type checker to work with
  types defined in other packages

After adding a new dependency, you can run `make update`


```shell
(myproject_py36) dev@host:~/myproject
$ make update
Solving environment: done

Downloading and Extracting Packages
requests-2.19.1        | 94 KB  conda-forge
...
```

Normally make update only does something if you update one of the
`requirements/*.txt` files has changed. If you know a dependency
was updated, and `make update` is not having an effect, you can
force the update using `make force update`.


### Vendoring

Vendored dependencies are usually committed to git, but if you
trust the package maintainer and the installation via `vendor.txt`,
then it's not required.

There are a few reasons to vendor a dependency:

1. You want the source to be easilly accessible in your development
   tools. For example mypy can access the types of vendored projects.
2. You don't trust the maintainer of a dependency, and want to review
   any updates using git diff.
3. There is no maintainer or downloadable package, so your only option
   is to download it into a local directory. For example you may want to
   use some of the modules from https://github.com/TheAlgorithms/Python

If you do vendor a dependency, avoid local modifications, instead
contribute to the upstream project when possible.


## Development

The typical commands used during development are:

- `make install`: Setup virtual environment
- `source activate`: Activate virtual environment
- `make help`: Overview of tasks
- `make fmt`: Format code
- `make lint`: Linting
- `make mypy`: Typecheck
- `make devtest`: Run unittests with dev interpreter against code from `src/`.

Slightly less common but good to run before doing `git push`.

- `make test`: Run unitests on all supported interpreters after installing
  using `python setup.py install`. This tests the code as the users of your
  library will have installed.
- `make citest`: Run `make test` but inside a docker container, which is as
  close to the ci environment as possible. This is quite useful if you don't
  want to trigger dozens of CI builds to debug a tricky issue.


### Docker

The base image of the project is `docker_base.Dockerfile` which is
used to create images that have only the conda virtual environment needed
to run the project. The CI environment uses the image generated by
`make docker_build`. While this means that the CI setup is simpler and faster,
as you don't have to build the image for the test run in the CI environment, it does mean that you have to run `make docker_build` every time one of your dependencies is updated.

The `docker_base.Dockerfile` uses the multi stage builder pattern, so that 1.
your private key doesn't end up in the published image 2. the published image
is as small as possible.


```
$ make docker_build
Sending build context to Docker daemon  7.761MB
Step 1/20 : FROM registry.gitlab.com/mbarkhau/bootstrapit/env_builder AS builder
...
conda create --name myproject_py36 python=3.6 ...
Solving environment: ...working... done
...
conda create --name myproject_py35 python=3.5 ...
Solving environment: ...working... done

docker push
```

As is the case for your local development setup, every version of python
that you have configured to be supported, is installed in the image. If
you want to create a minimal image for a production system, you may wish
to trim this down.


### Documentation


Documentation is written in Github Flavoured Markdown. Typora is
decent cross platform editor.

TODO: `make doc`


### Editor Setup

https://gitlab.com/mbarkhau/straitjacket#editortooling-integration

TODO: Expand how to set editor, possibly by sharing editor config files?


## Best Practices

While not all practices linked here are followed (they are
contradictory to each other in places), reading them will give you a
good overview of how different people think about structuring their
code in order to minimize common pitfalls.

Please read, view at your leasure:

 - Talks:
   - [Stop Writing Classes by Jack Diederich](https://www.youtube.com/watch?v=o9pEzgHorH0)
   - [The Naming of Ducks: Where Dynamic Types Meet Smart Conventions by Brandon Rhodes](https://www.youtube.com/watch?v=YklKUuDpX5c)
   - [Transforming Code into Beautiful, Idiomatic Python by Raymond Hettinger](https://www.youtube.com/watch?v=OSGv2VnC0go)
   - [Beyond PEP 8 -- Best practices for beautiful intelligible code by Raymond Hettinger](https://www.youtube.com/watch?v=wf-BqAjZb8M)
 - Articles, Essays, Books:
   - Short ebook for Novice to Intermediate Pythonistas:
     [How to Make Mistakes in Python](https://www.oreilly.com/programming/free/how-to-make-mistakes-in-python.csp)
   - [The Little Book of Python Anti-Patterns](https://docs.quantifiedcode.com/python-anti-patterns/)
 - Style Guides:
   - https://www.python.org/dev/peps/pep-0008/
   - https://github.com/amontalenti/elements-of-python-style
   - https://github.com/google/styleguide/blob/gh-pages/pyguide.md

Keep in mind, that all of this is about the form of your code, and
catching common pitfalls or gotchas. None of this releives you of the
burdon of thinking about your code. The reason to use linters and type
checking is not to have a tool to make your code correct, but to
support you to make your code correct.

For now I won't go into the effort of writing yet another style guide.
Instead, if your code passes `make fmt lint`, then it's acceptable.
Every time you encounter a linting error, consider it as an opportinity
to learn a best practice and look up the error code.

[^1]: Linux, MacOS and [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
