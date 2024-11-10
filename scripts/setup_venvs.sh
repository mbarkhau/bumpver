#!/bin/bash

read -r -a venv_names <<< "${VENV_NAMES//, /$IFS}";
read -r -a venv_py_paths <<< "${VENV_PYTHON_PATHS//, /$IFS}";
read -r -a py_versions <<< "${SUPPORTED_PYTHON_VERSIONS//, /$IFS}";

for i in ${!venv_py_paths[@]}; do
    env_path_python=${venv_py_paths[i]};
    env_name=${venv_names[i]};
    py_version=${py_versions[i]};

    echo ""
    echo ${env_path_python};
    echo ${py_version};
    echo "";

    if [[ ! -f ${env_path_python} ]]; then
        echo "uv venv ${env_name} --python ${py_version} ...";
        uv venv  --python ${py_version} ${env_name};
        uv install ${env_name} --yes --channel conda-forge ${py_version};
    fi;

    ${env_path_python} -m ensurepip;

    ${env_path_python} --version >> build/envs.txt.tmp \
        2>>build/envs.txt.tmp \
        1>>build/envs.txt.tmp;

done;
