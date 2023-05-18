#!/bin/bash
# Bootstrapit Project Configuration

AUTHOR_NAME="Manuel Barkhau"
AUTHOR_EMAIL="mbarkhau@gmail.com"

KEYWORDS="version bumpver calver semver versioning bumpversion pep440"
DESCRIPTION="Bump version numbers in project files."

LICENSE_ID="MIT"

PACKAGE_NAME="bumpver"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="github.com"

PACKAGE_VERSION="2023.1124"

DEFAULT_PYTHON_VERSION="python=3.8"
SUPPORTED_PYTHON_VERSIONS="python=2.7 python=3.6 pypy2.7 pypy3.5 python=3.8"

DOCKER_REGISTRY_DOMAIN=registry.gitlab.com


IS_PUBLIC=1

## Download and run the actual update script

PROJECT_DIR=$(dirname $0)

if ! [[ -f $PROJECT_DIR/scripts/bootstrapit_update.sh ]]; then
    mkdir -p "$PROJECT_DIR/scripts/";
    RAW_FILES_URL="https://gitlab.com/mbarkhau/bootstrapit/raw/master";
    curl --silent "$RAW_FILES_URL/scripts/bootstrapit_update.sh" \
        > "$PROJECT_DIR/scripts/bootstrapit_update.sh"
fi

source $PROJECT_DIR/scripts/bootstrapit_update.sh;
