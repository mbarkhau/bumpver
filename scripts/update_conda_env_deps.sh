#!/bin/bash

read -r -a env_py_paths <<< "${CONDA_ENV_BIN_PYTHON_PATHS//, /$IFS}";
read -r -a env_names <<< "${CONDA_ENV_NAMES//, /$IFS}";

for i in ${!env_py_paths[@]}; do
    env_path_python=${env_py_paths[i]};
    env_name=${env_names[i]};

    ${env_path_python} -m pip install --upgrade --quiet pip;

    echo "updating ${env_name} pypi deps ...";

    # pytest is required in every environment to run the test suite
    # against the installed modules.
    ${env_path_python} -m pip install \
        --disable-pip-version-check --upgrade --quiet \
        pytest;

    ${env_path_python} -m pip install \
        --disable-pip-version-check --upgrade --quiet \
        --requirement=requirements/pypi.txt;

    echo "updating ${env_name} vendor deps ...";

    ${env_path_python} -m pip install \
        --disable-pip-version-check --upgrade --quiet \
        --requirement=requirements/vendor.txt;
done;
