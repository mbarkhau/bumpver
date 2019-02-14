#!/bin/bash

set -Ee -o pipefail;
shopt -s extglob nocasematch;

BOOTSTRAPIT_GIT_URL="https://gitlab.com/mbarkhau/bootstrapit.git/"

BOOTSTRAPIT_GIT_PATH=/tmp/bootstrapit;

echo "Updating from $BOOTSTRAPIT_GIT_URL";

if [[ ! -e "$BOOTSTRAPIT_GIT_PATH" ]]; then
    git clone "$BOOTSTRAPIT_GIT_URL" "$BOOTSTRAPIT_GIT_PATH";
else
    OLD_PWD="$PWD";
    cd "$BOOTSTRAPIT_GIT_PATH";
    git pull --quiet;
    cd "$OLD_PWD";
fi

BOOTSTRAPIT_DEBUG=0

if [[ $BOOTSTRAPIT_DEBUG == 0 ]]; then
    if [[ -f "$PROJECT_DIR/.git/config" ]]; then
        OLD_PWD="$PWD"
        cd "$PROJECT_DIR";
        if [[ $( git diff -s --exit-code || echo "$?" ) -gt 0 ]]; then
            echo "ABORTING!: Your repo has local changes which are not comitted."
            echo "To avoid overwriting these changes, please commit your changes."
            exit 1;
        fi
        cd "$OLD_PWD";
    fi

    md5sum=$(which md5sum || which md5)

    old_md5=$( cat "$PROJECT_DIR/scripts/bootstrapit_update.sh" | $md5sum );
    new_md5=$( cat "$BOOTSTRAPIT_GIT_PATH/scripts/bootstrapit_update.sh" | $md5sum );

    if [[ "$old_md5" != "$new_md5" ]]; then
        # Copy the updated file, run it and exit the current execution.
        cp "${BOOTSTRAPIT_GIT_PATH}/scripts/bootstrapit_update.sh" \
            "${PROJECT_DIR}/scripts/";
        git add "${PROJECT_DIR}/scripts/bootstrapit_update.sh";
        git commit --no-verify -m "auto update of scripts/bootstrapit_update.sh"
        # shellcheck source=scripts/bootstrapit_update.sh
        source "${PROJECT_DIR}/scripts/bootstrapit_update.sh";
        exit 0;
    fi
fi


# Argument parsing from
# https://stackoverflow.com/a/14203146/62997
UPDATE_ALL=0

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -a|--all)
    UPDATE_ALL=1
    shift # past argument
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done

set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ -z $AUTHOR_EMAIL && ! -z $AUTHOR_CONTACT ]]; then
    AUTHOR_EMAIL="${AUTHOR_CONTACT}"
fi

YEAR=$(date +%Y)
MONTH=$(date +%m)

declare -a required_config_param_names=(
    "AUTHOR_NAME"
    "AUTHOR_EMAIL"
    "PACKAGE_NAME"
    "IS_PUBLIC"
    "GIT_REPO_NAMESPACE"
    "GIT_REPO_DOMAIN"
    "DESCRIPTION"
    "KEYWORDS"
    "LICENSE_ID"
)

for name in "${required_config_param_names[@]}"; do
    if [[ -z ${!name} ]]; then
        echo "Missing parameter $name in $1";
        exit 1;
    fi
done

if [[ -z $MODULE_NAME ]]; then
    MODULE_NAME=${PACKAGE_NAME};
fi

if [[ -z $PACKAGE_VERSION ]]; then
    PACKAGE_VERSION="$(date +'v%Y%m.0001-alpha')"
fi

if [[ -z $DEFAULT_PYTHON_VERSION ]]; then
    DEFAULT_PYTHON_VERSION="python=3.6";
fi

if [[ -z $SUPPORTED_PYTHON_VERSIONS ]]; then
    SUPPORTED_PYTHON_VERSIONS=${DEFAULT_PYTHON_VERSION};
fi

if [[ -z $SPDX_LICENSE_ID ]]; then
    if [[ $LICENSE_ID =~ none ]]; then
        SPDX_LICENSE_ID="Proprietary";
    else
        SPDX_LICENSE_ID=$LICENSE_ID;
    fi
fi


SPDX_REPO_URL="https://raw.githubusercontent.com/spdx";
LICENSE_TXT_URL="$SPDX_REPO_URL/license-list-data/master/text/${SPDX_LICENSE_ID}.txt";
LICENSE_XML_URL="$SPDX_REPO_URL/license-list-XML/master/src/${SPDX_LICENSE_ID}.xml";

LICENSE_TXT_FILE="/tmp/bootstrapit_$LICENSE_ID.txt"
LICENSE_XML_FILE="/tmp/bootstrapit_$LICENSE_ID.xml"


if ! [[ $LICENSE_ID =~ none ]]; then
    if ! [[ -f "$LICENSE_TXT_FILE" ]]; then
        echo "Downloading license text from $LICENSE_TXT_URL"
        curl -L --silent "$LICENSE_TXT_URL" > "$LICENSE_TXT_FILE.tmp";
        mv "$LICENSE_TXT_FILE.tmp" "$LICENSE_TXT_FILE";
    fi
    if ! [[ -f "$LICENSE_XML_FILE" ]]; then
        echo "Downloading license info from $LICENSE_XML_URL"
        curl -L --silent "$LICENSE_XML_URL" > "$LICENSE_XML_FILE.tmp";
        mv "$LICENSE_XML_FILE.tmp" "$LICENSE_XML_FILE";
    fi
fi


if [[ -z $LICENSE_NAME ]]; then
    if [[ $LICENSE_ID =~ none ]]; then
        LICENSE_NAME="All Rights Reserved";
    else
        LICENSE_NAME=$(
             awk '{ if ($0 ~ /[^>]\s*$/ ) { printf "%s", $0 } else {printf "%s\n", $0 } }' \
             "$LICENSE_XML_FILE" \
             | grep "<license" \
             | sed -E 's/.*name="([A-Za-z0-9[:punct:][:space:]]+)".*/\1/g' \
             | sed 's/&#34;/"/g' \
             | head -n 1
        )
    fi
fi


if [[ -z $LICENSE_CLASSIFIER ]]; then
    if [[ $LICENSE_ID =~ none ]]; then
        LICENSE_CLASSIFIER="License :: Other/Proprietary License";
    elif [[ $LICENSE_ID =~ mit ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: MIT License";
    elif [[ $LICENSE_ID =~ bsd ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: BSD License";
    elif [[ $LICENSE_ID =~ gpl-2.0-only ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: GNU General Public License v2 (GPLv2)";
    elif [[ $LICENSE_ID =~ lgpl-2.0-only ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)";
    elif [[ $LICENSE_ID =~ gpl-3.0-only ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: GNU General Public License v3 (GPLv3)";
    elif [[ $LICENSE_ID =~ agpl-3.0-only ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: GNU Affero General Public License v3";
    elif [[ $LICENSE_ID =~ lgpl-3.0-only ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)";
    elif [[ $LICENSE_ID =~ mpl-2.0 ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)";
    elif [[ $LICENSE_ID =~ apache-2.0 ]]; then
        LICENSE_CLASSIFIER="License :: OSI Approved :: Apache Software License";
    else
        echo "Invalid LICENSE_ID=\"$LICENSE_ID\". Could not determine LICENSE_CLASSIFIER.";
        exit 1;
    fi
fi

if [[ -z "$COPYRIGHT_STRING" ]]; then
    COPYRIGHT_STRING="Copyright (c) ${YEAR} ${AUTHOR_NAME} (${AUTHOR_EMAIL}) - ${LICENSE_NAME}";
fi

if [[ -z "$SETUP_PY_LICENSE" ]]; then
    if [[ $LICENSE_ID =~ none ]]; then
        SETUP_PY_LICENSE="$COPYRIGHT_STRING";
    else
        SETUP_PY_LICENSE=$SPDX_LICENSE_ID;
    fi
fi


if [[ -z "$IS_PUBLIC" ]]; then
    IS_PUBLIC=$( echo "$GIT_REPO_DOMAIN" | grep -c -E '(gitlab\.com|github\.com|bitbucket\.org)' || true );
fi

if [[ -z "$PAGES_DOMAIN" ]]; then
    if [[ "$GIT_REPO_DOMAIN" == "gitlab.com" ]]; then
        PAGES_DOMAIN=gitlab.io;
    elif [[ "$GIT_REPO_DOMAIN" == "github.com" ]]; then
        PAGES_DOMAIN=github.io;
    elif [[ "$GIT_REPO_DOMAIN" == "bitbucket.org" ]]; then
        PAGES_DOMAIN=bitbucket.io;
    else
        PAGES_DOMAIN="gitlab-pages.$GIT_REPO_DOMAIN";
    fi
fi

if [[ -z "$PAGES_URL" ]]; then
    PAGES_URL="https://${GIT_REPO_NAMESPACE}.${PAGES_DOMAIN}/${PACKAGE_NAME}/"
fi

if [[ -z "$DOCKER_REGISTRY_DOMAIN" ]]; then
    if [[ "$GIT_REPO_DOMAIN" == "gitlab.com" ]]; then
        DOCKER_REGISTRY_DOMAIN=registry.gitlab.com;
    else
        DOCKER_REGISTRY_DOMAIN=hub.docker.com;
    fi
fi

if [[ -z "$DOCKER_ROOT_IMAGE" ]]; then
    DOCKER_ROOT_IMAGE=registry.gitlab.com/mbarkhau/bootstrapit/root
fi

if [[ -z "$DOCKER_ENV_BUILDER_IMAGE" ]]; then
    DOCKER_ENV_BUILDER_IMAGE=registry.gitlab.com/mbarkhau/bootstrapit/env_builder
fi

if [[ -z "$DOCKER_REGISTRY_URL" ]]; then
    DOCKER_REGISTRY_URL=${DOCKER_REGISTRY_DOMAIN}/${GIT_REPO_NAMESPACE}/${PACKAGE_NAME}
fi

if [[ -z "$DOCKER_BASE_IMAGE" ]]; then
    DOCKER_BASE_IMAGE=${DOCKER_REGISTRY_URL}/base
fi

# strip off ":latest"
# https://medium.com/@mccode/the-misunderstood-docker-tag-latest-af3babfd6375
# https://vsupalov.com/docker-latest-tag/
DOCKER_BASE_IMAGE="$(dirname ${DOCKER_BASE_IMAGE})"/"$(basename ${DOCKER_BASE_IMAGE} ':latest')";

if [[ -z "$MODULE_NAME" ]]; then
    MODULE_NAME=$( echo "${PACKAGE_NAME}" | tr '[:upper:]' '[:lower:]' | sed -E -e 's;-;_;g'; );
fi

if [[ -z "$GIT_REPO_URL" ]]; then
    GIT_REPO_URL=https://${GIT_REPO_DOMAIN}/${GIT_REPO_NAMESPACE}/${PACKAGE_NAME}
elif [[ ! "$GIT_REPO_URL" =~ ^https?://[^/]+/[^/]+/[^/]+(/|.git)?$ ]]; then
    echo "ERROR: Invalid argument for '${GIT_REPO_URL}'";
    exit 1;
fi

GIT_REPO_PATH=$( echo "$GIT_REPO_URL" | sed -E -e 's;https?://[^/]+/;;g' | sed -E 's;(/|.git)$;;g' )
GIT_REPO_NAME=$( echo "$GIT_REPO_PATH" | sed -E -e 's;^[A-Za-z_-]+/;;g' )

if [[ "$LICENSE_ID" =~ "none" ]]; then
    echo "$COPYRIGHT_STRING" > "$PROJECT_DIR/LICENSE";
else
    cat "$LICENSE_TXT_FILE" \
        | sed "s/Copyright (c) <year> <owner>[[:space:]]*/Copyright (c) $YEAR $AUTHOR_NAME ($AUTHOR_EMAIL)/g" \
        | sed "s/Copyright (c) <year> <copyright holders>[[:space:]]*/Copyright (c) $YEAR $AUTHOR_NAME ($AUTHOR_EMAIL)/g" \
        > "$PROJECT_DIR/LICENSE";
fi

function format_template()
{
    cat "$1" \
        | sed "s;\${GIT_REPO_URL};${GIT_REPO_URL};g" \
        | sed "s;\${GIT_REPO_PATH};${GIT_REPO_PATH};g" \
        | sed "s;\${GIT_REPO_NAMESPACE};${GIT_REPO_NAMESPACE};g" \
        | sed "s;\${GIT_REPO_NAME};${GIT_REPO_NAME};g" \
        | sed "s;\${GIT_REPO_DOMAIN};${GIT_REPO_DOMAIN};g" \
        | sed "s;\${DEFAULT_PYTHON_VERSION};${DEFAULT_PYTHON_VERSION};g" \
        | sed "s;\${SUPPORTED_PYTHON_VERSIONS};${SUPPORTED_PYTHON_VERSIONS};g" \
        | sed "s;\${DOCKER_REGISTRY_DOMAIN};${DOCKER_REGISTRY_DOMAIN};g" \
        | sed "s;\${DOCKER_REGISTRY_URL};${DOCKER_REGISTRY_URL};g" \
        | sed "s;\${DOCKER_ROOT_IMAGE};${DOCKER_ROOT_IMAGE};g" \
        | sed "s;\${DOCKER_ENV_BUILDER_IMAGE};${DOCKER_ENV_BUILDER_IMAGE};g" \
        | sed "s;\${DOCKER_BASE_IMAGE};${DOCKER_BASE_IMAGE};g" \
        | sed "s;\${PAGES_DOMAIN};${PAGES_DOMAIN};g" \
        | sed "s;\${PAGES_URL};${PAGES_URL};g" \
        | sed "s;\${AUTHOR_CONTACT};${AUTHOR_CONTACT};g" \
        | sed "s;\${AUTHOR_EMAIL};${AUTHOR_EMAIL};g" \
        | sed "s;\${AUTHOR_NAME};${AUTHOR_NAME};g" \
        | sed "s;\${PACKAGE_NAME};${PACKAGE_NAME};g" \
        | sed "s;\${PACKAGE_VERSION};${PACKAGE_VERSION};g" \
        | sed "s;\${MODULE_NAME};${MODULE_NAME};g" \
        | sed "s;\${DESCRIPTION};${DESCRIPTION};g" \
        | sed "s;\${KEYWORDS};${KEYWORDS};g" \
        | sed "s;\${SPDX_LICENSE_ID};${SPDX_LICENSE_ID};g" \
        | sed "s;\${SETUP_PY_LICENSE};${SETUP_PY_LICENSE};g" \
        | sed "s;\${LICENSE_CLASSIFIER};${LICENSE_CLASSIFIER};g" \
        | sed "s;\${COPYRIGHT_STRING};${COPYRIGHT_STRING};g" \
        | sed "s;\${YEAR};${YEAR};g" \
        | sed "s;\${MONTH};${MONTH};g" \
        | sed "s;\${IS_PUBLIC};${IS_PUBLIC};g" \
        > "$1.tmp";
    mv "$1.tmp" "$1";
}

if [[ "${UPDATE_ALL}" -eq "1" ]]; then
    declare -a IGNORE_IF_EXISTS=()
elif [[ -z "${IGNORE_IF_EXISTS[*]}" ]]; then
    declare -a IGNORE_IF_EXISTS=(
        "CHANGELOG.md"
        "README.md"
        "setup.py"
        "makefile.config.make"
        "requirements/pypi.txt"
        "requirements/development.txt"
        "requirements/conda.txt"
        "requirements/vendor.txt"
        "src/${MODULE_NAME}/__init__.py"
        "src/${MODULE_NAME}/__main__.py"
    )
fi

function copy_template()
{
    if [[ -z ${2} ]]; then
        dest_subpath=$1;
    else
        dest_subpath=$2;
    fi

    dest_path=${PROJECT_DIR}/$dest_subpath;
    if [[ -f "$dest_subpath" ]]; then
        for ignore_item in "${IGNORE_IF_EXISTS[@]}"; do
            if [[ "$dest_subpath" == "$ignore_item" ]]; then
                return 0;
            fi
        done
    fi

    cat "${BOOTSTRAPIT_GIT_PATH}/$1.template" > "$dest_path";

    format_template "$dest_path";
}

mkdir -p "${PROJECT_DIR}/test/";
mkdir -p "${PROJECT_DIR}/vendor/";
mkdir -p "${PROJECT_DIR}/scripts/";
mkdir -p "${PROJECT_DIR}/stubs/";
mkdir -p "${PROJECT_DIR}/src/";
mkdir -p "${PROJECT_DIR}/requirements/";
mkdir -p "${PROJECT_DIR}/src/${MODULE_NAME}";

copy_template .gitignore;
copy_template README.md;
copy_template CONTRIBUTING.md;
copy_template CHANGELOG.md;
copy_template license.header;
copy_template stubs/README.md;
copy_template MANIFEST.in;

copy_template setup.py;
copy_template setup.cfg;

copy_template makefile;
copy_template makefile.config.make;
copy_template makefile.extra.make;
copy_template activate;
copy_template docker_base.Dockerfile;
copy_template Dockerfile;

copy_template requirements/conda.txt;
copy_template requirements/pypi.txt;
copy_template requirements/development.txt;
copy_template requirements/integration.txt;
copy_template requirements/vendor.txt;

copy_template .gitlab-ci.yml;
copy_template scripts/update_conda_env_deps.sh;
copy_template scripts/setup_conda_envs.sh;
copy_template scripts/pre-push-hook.sh;

copy_template __main__.py "src/${MODULE_NAME}/__main__.py";
copy_template __init__.py "src/${MODULE_NAME}/__init__.py";
touch "${PROJECT_DIR}/test/__init__.py";

chmod +x "${PROJECT_DIR}/src/${MODULE_NAME}/__main__.py";
chmod +x "${PROJECT_DIR}/scripts/update_conda_env_deps.sh";
chmod +x "${PROJECT_DIR}/scripts/setup_conda_envs.sh";
chmod +x "${PROJECT_DIR}/scripts/pre-push-hook.sh";

head -n 7 "${PROJECT_DIR}/license.header" \
    | tail -n +3 \
    | sed -re 's/(^   |^$)/#/g' \
    > /tmp/.py_license.header;

src_files="${PROJECT_DIR}/src/*/*.py"

for src_file in $src_files; do
    if grep -q -E '^# SPDX-License-Identifier' "$src_file"; then
        continue;
    fi
    offset=0
    if grep -z -q -E '^#![/a-z ]+?python' "$src_file"; then
        let offset+=1;
    fi
    if grep -q -E '^# .+?coding: [a-zA-Z0-9_\-]+' "$src_file"; then
        let offset+=1;
    fi
    rm -f "${src_file}.with_header";
    if [[ $offset -gt 0 ]]; then
        head -n $offset "${src_file}" > "${src_file}.with_header";
    fi
    let offset+=1;
    cat /tmp/.py_license.header >> "${src_file}.with_header";
    tail -n +$offset "${src_file}" >> "${src_file}.with_header";
    mv "${src_file}.with_header" "$src_file";
done

rm /tmp/.py_license.header;

git status;
