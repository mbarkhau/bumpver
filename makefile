# Helpful Links

# http://clarkgrubb.com/makefile-style-guide
# https://explainshell.com
# https://stackoverflow.com/questions/448910
# https://shiroyasha.svbtle.com/escape-sequences-a-quick-guide-1

SHELL := /bin/bash
.SHELLFLAGS := -O extglob -eo pipefail -c
.DEFAULT_GOAL := help
.SUFFIXES:

-include makefile.config.make

PROJECT_DIR := $(notdir $(abspath .))

ifndef DEVELOPMENT_PYTHON_VERSION
	DEVELOPMENT_PYTHON_VERSION := python=3.6
endif

ifndef SUPPORTED_PYTHON_VERSIONS
	SUPPORTED_PYTHON_VERSIONS := $(DEVELOPMENT_PYTHON_VERSION)
endif

PKG_NAME := $(PACKAGE_NAME)

# TODO (mb 2018-09-23): Support for bash on windows
#    perhaps we need to install conda using this
#    https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe
PLATFORM = $(shell uname -s)

# miniconda is shared between projects
CONDA_ROOT := $(shell if [[ -d /opt/conda/envs ]]; then echo "/opt/conda"; else echo "$$HOME/miniconda3"; fi;)
CONDA_BIN := $(CONDA_ROOT)/bin/conda

ENV_PREFIX := $(CONDA_ROOT)/envs

DEV_ENV_NAME := \
	$(subst pypy,$(PKG_NAME)_pypy,$(subst python=,$(PKG_NAME)_py,$(subst .,,$(DEVELOPMENT_PYTHON_VERSION))))

CONDA_ENV_NAMES := \
	$(subst pypy,$(PKG_NAME)_pypy,$(subst python=,$(PKG_NAME)_py,$(subst .,,$(SUPPORTED_PYTHON_VERSIONS))))

CONDA_ENV_PATHS := \
	$(subst pypy,${ENV_PREFIX}/$(PKG_NAME)_pypy,$(subst python=,${ENV_PREFIX}/$(PKG_NAME)_py,$(subst .,,$(SUPPORTED_PYTHON_VERSIONS))))


literal_space := $() $()

BDIST_WHEEL_PYTHON_TAG := \
	$(subst python,py,$(subst $(literal_space),.,$(subst .,,$(subst =,,$(SUPPORTED_PYTHON_VERSIONS)))))

SDIST_FILE_CMD = ls -1t dist/*.tar.gz | head -n 1

BDIST_WHEEL_FILE_CMD = ls -1t dist/*.whl | head -n 1


# default version for development
DEV_ENV := $(ENV_PREFIX)/$(DEV_ENV_NAME)
DEV_ENV_PY := $(DEV_ENV)/bin/python

RSA_KEY_PATH := ${HOME}/.ssh/${PKG_NAME}_gitlab_runner_id_rsa

DOCKER_BASE_IMAGE := registry.gitlab.com/mbarkhau/pycalver/base

DOCKER_IMAGE_VERSION := $(shell date -u +'%Y%m%dt%H%M%S')_$(shell git rev-parse --short HEAD)


build/envs.txt: requirements/conda.txt
	@mkdir -p build/;

	@if [[ ! -f $(CONDA_BIN) ]]; then \
		echo "installing miniconda ..."; \
		if [[ $(PLATFORM) == "Linux" ]]; then \
			curl "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh" \
				> build/miniconda3.sh; \
		elif [[ $(PLATFORM) == "MINGW64_NT-10.0" ]]; then \
			curl "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh" \
				> build/miniconda3.sh; \
		elif [[ $(PLATFORM) == "Darwin" ]]; then \
			curl "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh" \
				> build/miniconda3.sh; \
		fi; \
		bash build/miniconda3.sh -b -p $(CONDA_ROOT); \
		rm build/miniconda3.sh; \
	fi

	rm -f build/envs.txt.tmp;

	@SUPPORTED_PYTHON_VERSIONS="$(SUPPORTED_PYTHON_VERSIONS)" \
		CONDA_ENV_NAMES="$(CONDA_ENV_NAMES)" \
		CONDA_ENV_PATHS="$(CONDA_ENV_PATHS)" \
		CONDA_BIN="$(CONDA_BIN)" \
		bash scripts/setup_conda_envs.sh;

	$(CONDA_BIN) env list \
		| grep $(PKG_NAME) \
		| rev | cut -d " " -f1 \
		| rev | sort >> build/envs.txt.tmp;

	mv build/envs.txt.tmp build/envs.txt;


build/deps.txt: build/envs.txt requirements/*.txt
	@mkdir -p build/;

	@SUPPORTED_PYTHON_VERSIONS="$(SUPPORTED_PYTHON_VERSIONS)" \
		CONDA_ENV_NAMES="$(CONDA_ENV_NAMES)" \
		CONDA_ENV_PATHS="$(CONDA_ENV_PATHS)" \
		CONDA_BIN="$(CONDA_BIN)" \
		bash scripts/update_conda_env_deps.sh;

	@echo "updating $(DEV_ENV_NAME) development deps ...";

	@$(DEV_ENV_PY) -m pip install \
		--disable-pip-version-check --upgrade \
		--requirement=requirements/integration.txt;

	@$(DEV_ENV_PY) -m pip install \
		--disable-pip-version-check --upgrade \
		--requirement=requirements/development.txt;

	@echo "updating local vendor dep copies ...";

	@$(DEV_ENV_PY) -m pip install \
		--upgrade --disable-pip-version-check \
		--no-deps --target=./vendor \
		--requirement=requirements/vendor.txt;

	@rm -f build/deps.txt.tmp;

	@for env_name in $(CONDA_ENV_NAMES); do \
		env_py="${ENV_PREFIX}/$${env_name}/bin/python"; \
		printf "\npip freeze for $${env_name}:\n" >> build/deps.txt.tmp; \
		$${env_py} -m pip freeze >> build/deps.txt.tmp; \
		printf "\n\n" >> build/deps.txt.tmp; \
	done

	@mv build/deps.txt.tmp build/deps.txt


## Short help message for each task.
.PHONY: help
help:
	@awk '{ \
			if ($$0 ~ /^.PHONY: [a-zA-Z\-\_0-9]+$$/) { \
				helpCommand = substr($$0, index($$0, ":") + 2); \
				if (helpMessage) { \
					printf "\033[36m%-20s\033[0m %s\n", \
						helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^[a-zA-Z\-\_0-9.]+:/) { \
				helpCommand = substr($$0, 0, index($$0, ":")); \
				if (helpMessage) { \
					printf "\033[36m%-20s\033[0m %s\n", \
						helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^##/) { \
				if (! (helpMessage)) { \
					helpMessage = substr($$0, 3); \
				} \
			} else { \
				if (helpMessage) { \
					print "                     "helpMessage \
				} \
				helpMessage = ""; \
			} \
		}' \
		$(MAKEFILE_LIST)

	@if [[ ! -f $(DEV_ENV_PY) ]]; then \
	echo "Missing python interpreter at $(DEV_ENV_PY) !"; \
	echo "You problably want to install first:"; \
	echo ""; \
	echo "    make install"; \
	echo ""; \
	exit 0; \
	fi

	@if [[ ! -f $(CONDA_BIN) ]]; then \
	echo "No conda installation found!"; \
	echo "You problably want to install first:"; \
	echo ""; \
	echo "    make install"; \
	echo ""; \
	exit 0; \
	fi


## Full help message for each task.
.PHONY: fullhelp
fullhelp:
	@printf "Available make targets for \033[97m$(PKG_NAME)\033[0m:\n";

	@awk '{ \
			if ($$0 ~ /^.PHONY: [a-zA-Z\-\_0-9]+$$/) { \
				helpCommand = substr($$0, index($$0, ":") + 2); \
				if (helpMessage) { \
					printf "\033[36m%-20s\033[0m %s\n", \
						helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^[a-zA-Z\-\_0-9.]+:/) { \
				helpCommand = substr($$0, 0, index($$0, ":")); \
				if (helpMessage) { \
					printf "\033[36m%-20s\033[0m %s\n", \
						helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^##/) { \
				if (helpMessage) { \
					helpMessage = helpMessage"\n                     "substr($$0, 3); \
				} else { \
					helpMessage = substr($$0, 3); \
				} \
			} else { \
				if (helpMessage) { \
					print "\n                     "helpMessage"\n" \
				} \
				helpMessage = ""; \
			} \
		}' \
		$(MAKEFILE_LIST)


## -- Project Setup --


## Delete conda envs and cache 💩
.PHONY: clean
clean:
	@for env_name in $(CONDA_ENV_NAMES); do \
		env_py="${ENV_PREFIX}/$${env_name}/bin/python"; \
		if [[ -f $${env_py} ]]; then \
			$(CONDA_BIN) env remove --name $${env_name} --yes; \
		fi; \
	done

	rm -f build/envs.txt
	rm -f build/deps.txt
	rm -rf vendor/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf vendor/__pycache__/
	@printf "\n setup/update completed  ✨ 🍰 ✨ \n\n"


## Force update of dependencies by removing marker files
##   Use this when you know an external dependency was
##   updated, but that is not reflected in your
##   requirements files.
##
##   Usage: make force update
.PHONY: force
force:
	rm -f build/envs.txt
	rm -f build/deps.txt
	rm -rf vendor/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf vendor/__pycache__/


## Setup python virtual environments
.PHONY: install
install: build/deps.txt


## Update dependencies (pip install -U ...)
.PHONY: update
update: build/deps.txt


## Install git pre-push hooks
.PHONY: git_hooks
git_hooks:
	@rm -f "${PWD}/.git/hooks/pre-push"
	ln -s "${PWD}/scripts/pre-push-hook.sh" "${PWD}/.git/hooks/pre-push"


## -- Integration --


## Run flake8 linter
.PHONY: lint
lint:
	@printf "flake8 ..\n"
	@$(DEV_ENV)/bin/flake8 src/
	@printf "\e[1F\e[9C ok\n"


## Run mypy type checker
.PHONY: mypy
mypy:
	@rm -rf ".mypy_cache";

	@printf "mypy ....\n"
	@MYPYPATH=stubs/:vendor/ $(DEV_ENV_PY) -m mypy src/
	@printf "\e[1F\e[9C ok\n"


## Run pylint. Should not break the build yet
.PHONY: pylint
pylint:
	@printf "pylint ..\n";
	@$(DEV_ENV)/bin/pylint --jobs=4 --output-format=colorized --score=no \
		 --disable=C0103,C0301,C0330,C0326,C0330,C0411,R0903,W1619,W1618,W1203 \
		 --extension-pkg-whitelist=ujson,lxml,PIL,numpy,pandas,sklearn,pyblake2 \
		 src/
	@$(DEV_ENV)/bin/pylint --jobs=4 --output-format=colorized --score=no \
		 --disable=C0103,C0111,C0301,C0330,C0326,C0330,C0411,R0903,W1619,W1618,W1203 \
		 --extension-pkg-whitelist=ujson,lxml,PIL,numpy,pandas,sklearn,pyblake2 \
		 test/

	@printf "\e[1F\e[9C ok\n"


## Run pytest unit and integration tests
.PHONY: test
test:
	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";

	# First we test the local source tree using the dev environment
	ENV=$${ENV-dev} PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(DEV_ENV_PY) -m pytest -v \
		--doctest-modules \
		--verbose \
		--cov-report html \
		--cov-report term \
		$(shell cd src/ && ls -1 */__init__.py | awk '{ print "--cov "substr($$1,0,index($$1,"/")-1) }') \
		test/ src/;

	# Next we install the package and run the test suite against it.

	IFS=' ' read -r -a env_paths <<< "$(CONDA_ENV_PATHS)"; \
	for i in $${!env_paths[@]}; do \
		env_py=$${env_paths[i]}/bin/python; \
		$${env_py} -m pip install --upgrade .; \
		ENV=$${ENV-dev} $${env_py} -m pytest test/; \
	done;

	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";


## -- Helpers --


## Run code formatter on src/ and test/
.PHONY: fmt
fmt:
	@$(DEV_ENV)/bin/sjfmt --py36 --skip-string-normalization --line-length=100 \
		 src/ test/


## Shortcut for make fmt lint pylint test
.PHONY: check
check:  fmt lint mypy test


## Start subshell with environ variables set.
.PHONY: env_subshell
env_subshell:
	@bash --init-file <(echo '\
		source $$HOME/.bashrc; \
		source $(CONDA_ROOT)/etc/profile.d/conda.sh \
		export ENV=$${ENV-dev}; \
		export PYTHONPATH="src/:vendor/:$$PYTHONPATH"; \
		conda activate $(DEV_ENV_NAME) \
	')


## Usage: "source activate", to deactivate: "deactivate"
.PHONY: activate
activate:
	@echo 'source $(CONDA_ROOT)/etc/profile.d/conda.sh;'
	@echo 'if [[ -z $$ENV ]]; then'
	@echo '		export _env_before_activate_$(DEV_ENV_NAME)=$${ENV};'
	@echo 'fi'
	@echo 'if [[ -z $$PYTHONPATH ]]; then'
	@echo '		export _pythonpath_before_activate_$(DEV_ENV_NAME)=$${PYTHONPATH};'
	@echo 'fi'
	@echo 'export ENV=$${ENV-dev};'
	@echo 'export PYTHONPATH="src/:vendor/:$$PYTHONPATH";'
	@echo 'conda activate $(DEV_ENV_NAME);'
	@echo 'function deactivate {'
	@echo '		if [[ -z $${_env_before_activate_$(DEV_ENV_NAME)} ]]; then'
	@echo '				export ENV=$${_env_before_activate_$(DEV_ENV_NAME)}; '
	@echo '		else'
	@echo '				unset ENV;'
	@echo '		fi'
	@echo '		if [[ -z $${_pythonpath_before_activate_$(DEV_ENV_NAME)} ]]; then'
	@echo '				export PYTHONPATH=$${_pythonpath_before_activate_$(DEV_ENV_NAME)}; '
	@echo '		else'
	@echo '				unset PYTHONPATH;'
	@echo '		fi'
	@echo '		conda deactivate;'
	@echo '};'


## Drop into an ipython shell with correct env variables set
.PHONY: ipy
ipy:
	@ENV=$${ENV-dev} PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(DEV_ENV)/bin/ipython


## Like `make test`, but with debug parameters
.PHONY: devtest
devtest:
	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";

ifdef FILTER
	ENV=$${ENV-dev} PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(DEV_ENV_PY) -m pytest -v \
		--doctest-modules \
		--no-cov \
		--verbose \
		--capture=no \
		--exitfirst \
		-k $(FILTER) \
		test/ src/;
else
	ENV=$${ENV-dev} PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(DEV_ENV_PY) -m pytest -v \
		--doctest-modules \
		--no-cov \
		--verbose \
		--capture=no \
		--exitfirst \
		test/ src/;
endif

	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";


## -- Build/Deploy --


# Generate Documentation
# .PHONY: doc
# doc:
# 	echo "Not Implemented"


## Freeze dependencies of the current development env.
##   The requirements files this produces should be used
##   in order to have reproducable builds, otherwise you
##   should minimize the number of pinned versions in
##   your requirements.
.PHONY: freeze
freeze:
	$(DEV_ENV_PY) -m pip freeze \
		> requirements/$(shell date -u +"%Y%m%dt%H%M%S")_freeze.txt


## Bump Version number in all files
.PHONY: bump_version
bump_version:
	echo "Not Implemented"
	# $(DEV_ENV)/bin/pycalver bump;


## Create python sdist and bdist_wheel files
.PHONY: build_dists
build_dists:
	$(DEV_ENV_PY) setup.py sdist;
	$(DEV_ENV_PY) setup.py bdist_wheel --python-tag=$(BDIST_WHEEL_PYTHON_TAG);


## Upload sdist and bdist files to pypi
.PHONY: upload_dists
upload_dists:
	@if [[ "1" != "1" ]]; then \
		echo "FAILSAFE! Not publishing a private package."; \
		echo "  To avoid this set IS_PUBLIC=1 in bootstrap.sh and run it."; \
		exit 1; \
	fi

	$(DEV_ENV)/bin/twine check $$($(SDIST_FILE_CMD));
	$(DEV_ENV)/bin/twine check $$($(BDIST_WHEEL_FILE_CMD));
	$(DEV_ENV)/bin/twine upload $$($(SDIST_FILE_CMD)) $$($(BDIST_WHEEL_FILE_CMD));


## Publish on pypi
.PHONY: publish
publish: bump_version build_dists upload_dists


## Build docker images. Must be run when dependencies are added
##   or updated. The main reasons this can fail are:
##   1. No ssh key at $(HOME)/.ssh/${PKG_NAME}_gitlab_runner_id_rsa
##      (which is needed to install packages from private repos
##      and is copied into a temp container during the build).
##   2. Your docker daemon is not running
##   3. You're using WSL and docker is not exposed on tcp://localhost:2375
##   4. You're using WSL but didn't do export DOCKER_HOST="tcp://localhost:2375"
.PHONY: build_docker
build_docker:
	@if [[ -f "${RSA_KEY_PATH}" ]]; then \
		docker build \
			--build-arg SSH_PRIVATE_RSA_KEY="$$(cat '${RSA_KEY_PATH}')" \
			--file docker_base.Dockerfile \
			--tag $(DOCKER_BASE_IMAGE):$(DOCKER_IMAGE_VERSION) \
			--tag $(DOCKER_BASE_IMAGE) \
			.; \
	else \
		docker build \
			--file docker_base.Dockerfile \
			--tag $(DOCKER_BASE_IMAGE):$(DOCKER_IMAGE_VERSION) \
			--tag $(DOCKER_BASE_IMAGE) \
			.; \
	fi

	docker push $(DOCKER_BASE_IMAGE)


## -- Extra/Custom/Project Specific Tasks --

-include makefile.extra.make
