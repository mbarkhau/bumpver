#!/bin/bash
# Bootstrapit Project Configuration

AUTHOR_NAME="Manuel Barkhau"
AUTHOR_CONTACT="@mbarkhau"

KEYWORDS="version versioning bumpversion calver"
DESCRIPTION="CalVer versioning for python libraries."

LICENSE_ID="MIT"

PACKAGE_NAME="pycalver"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="gitlab.com"

DEFAULT_PYTHON_VERSION="python=3.6"

IS_PUBLIC=1

## Download and run the actual update script

PROJECT_DIR=$(dirname $0)

if ! [[ -f $PROJECT_DIR/scripts/bootstrapit_update.sh ]]; then
    RAW_FILES_URL="https://gitlab.com/mbarkhau/bootstrapit/raw/master"
    mkdir -p "$PROJECT_DIR/scripts/";
    curl --silent -O "$PROJECT_DIR/scripts/bootstrapit_update.sh" \
        "$RAW_FILES_URL/scripts/bootstrapit_update.sh";
fi

source $PROJECT_DIR/scripts/bootstrapit_update.sh;
