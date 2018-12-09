#!/bin/bash
# Bootstrapit Project Configuration

AUTHOR_NAME="Manuel Barkhau"
AUTHOR_EMAIL="mbarkhau@gmail.com"

KEYWORDS="version versioning bumpversion calver"
DESCRIPTION="CalVer versioning for python libraries."

LICENSE_ID="MIT"

PACKAGE_NAME="pycalver"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="gitlab.com"

PACKAGE_VERSION="v201812.0008-beta"

DEFAULT_PYTHON_VERSION="python=3.6"
SUPPORTED_PYTHON_VERSIONS="python=2.7 python=3.5 python=3.6 python=3.7 pypy2.7 pypy3.5"

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
