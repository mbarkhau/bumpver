#!/bin/bash

read -r -a env_paths <<< "${CONDA_ENV_PATHS//, /$IFS}";
read -r -a env_names <<< "${CONDA_ENV_NAMES//, /$IFS}";

for i in ${!env_paths[@]}; do
    env_path=${env_paths[i]};
    env_path_python=${env_path}/bin/python;
    env_name=${env_names[i]};

    ${env_path_python} -m pip install --upgrade --quiet pip;

    echo "updating ${env_name} pypi deps ...";

    ${env_path_python} -m pip install \
        --disable-pip-version-check --upgrade --quiet \
        --requirement=requirements/pypi.txt;

    echo "updating ${env_name} vendor deps ...";

    ${env_path_python} -m pip install \
        --disable-pip-version-check --upgrade --quiet \
        --requirement=requirements/vendor.txt;
done;
