#!/bin/bash

read -r -a env_names <<< "${CONDA_ENV_NAMES//, /$IFS}";
read -r -a env_py_paths <<< "${CONDA_ENV_BIN_PYTHON_PATHS//, /$IFS}";
read -r -a py_versions <<< "${SUPPORTED_PYTHON_VERSIONS//, /$IFS}";

for i in ${!env_py_paths[@]}; do
    env_path_python=${env_py_paths[i]};
    env_name=${env_names[i]};
    py_version=${py_versions[i]};

    if [[ ! -f ${env_path_python} ]]; then
        echo "conda create --name ${env_name} ${py_version} ...";
        ${CONDA_BIN} create --name ${env_name} --channel conda-forge ${py_version} --yes --quiet;
    fi;

    echo "updating ${env_name} conda deps ...";
    ${CONDA_BIN} install --name ${env_name} --channel conda-forge --yes --quiet \
        $(grep -o '^[^#][^ ]*' requirements/conda.txt)

    ${env_path_python} -m ensurepip;

    ${env_path_python} --version >> build/envs.txt.tmp \
        2>>build/envs.txt.tmp \
        1>>build/envs.txt.tmp;

done;
