# Helpful Links

# http://clarkgrubb.com/makefile-style-guide
# https://explainshell.com
# https://stackoverflow.com/questions/448910
# https://shiroyasha.svbtle.com/escape-sequences-a-quick-guide-1

SHELL := /bin/bash
.SHELLFLAGS := -O extglob -eo pipefail -c
.DEFAULT_GOAL := help
.SUFFIXES:

PROJECT_DIR := $(notdir $(abspath .))

ifndef DEVELOPMENT_PYTHON_VERSION
	DEVELOPMENT_PYTHON_VERSION := python=3.13
endif

ifndef SUPPORTED_PYTHON_VERSIONS
	SUPPORTED_PYTHON_VERSIONS := $(DEVELOPMENT_PYTHON_VERSION)
endif

PKG_NAME := $(PACKAGE_NAME)
MODULE_NAME := $(shell echo $(subst -,_,$(PACKAGE_NAME)) | tr A-Z a-z)

HOME := $(shell echo $$HOME)
PLATFORM = $(shell uname -s)

VENVS_ROOT := $(HOME)/venvs

DEV_ENV_NAME := \
	$(subst pypy@,$(PKG_NAME)_pypy,$(subst python=,$(PKG_NAME)_py,$(subst .,,$(DEVELOPMENT_PYTHON_VERSION))))

VENV_NAMES := \
	$(subst pypy@,$(PKG_NAME)_pypy,$(subst python=,$(PKG_NAME)_py,$(subst .,,$(SUPPORTED_PYTHON_VERSIONS))))

VENV_PATHS := \
	$(subst pypy@,$(VENVS_ROOT)/$(PKG_NAME)_pypy,$(subst python=,$(VENVS_ROOT)/$(PKG_NAME)_py,$(subst .,,$(SUPPORTED_PYTHON_VERSIONS))))

# envname/bin/python is unfortunately not always the correct
# interpreter. In the case of pypy it is either envname/bin/pypy or
# envname/bin/pypy3
VENV_PYTHON_PATHS := \
	$(shell echo "$(VENV_PATHS)" \
	| sed 's!\(_py[[:digit:]]\{1,\}\)!\1/bin/python!g' \
	| sed 's!\(_pypy2[[:digit:]]\{1,\}\)!\1/bin/pypy!g' \
	| sed 's!\(_pypy3[[:digit:]]\{1,\}\)!\1/bin/pypy3!g' \
)

empty :=
literal_space := $(empty) $(empty)

BDIST_WHEEL_PYTHON_TAG := py2.py3

SDIST_FILE_CMD = ls -1t dist/*.tar.gz | head -n 1

BDIST_WHEEL_FILE_CMD = ls -1t dist/*.whl | head -n 1


# default version for development
DEV_ENV := $(VENVS_ROOT)/$(DEV_ENV_NAME)
DEV_ENV_PY := $(DEV_ENV)/bin/python

DOCKER := $(shell which docker)

DOCKER_BASE_IMAGE := registry.gitlab.com/mbarkhau/pycalver/base

GIT_HEAD_REV = $(shell git rev-parse --short HEAD)
DOCKER_IMAGE_VERSION = $(shell date -u +'%Y%m%dt%H%M%S')_$(GIT_HEAD_REV)

MAX_LINE_LEN = $(shell grep 'max-line-length' setup.cfg | sed 's![^0-9]\{1,\}!!')


build/envs.txt:
	@mkdir -p build/;

	@if [[ ! -f $(shell which uv) ]]; then \
		echo "installing uv ..."; \
		pip install uv; \
	fi

	@rm -f build/envs.txt.tmp;

	@SUPPORTED_PYTHON_VERSIONS="$(SUPPORTED_PYTHON_VERSIONS)" \
		VENV_NAMES="$(VENV_NAMES)" \
		VENV_PATHS="$(VENV_PATHS)" \
		VENV_PYTHON_PATHS="$(VENV_PYTHON_PATHS)" \
		bash scripts/setup_venvs.sh;

	ls -1 $(HOME)/venv \
		| grep $(PKG_NAME) \
		| rev | cut -d " " -f1 \
		| rev | sort >> build/envs.txt.tmp;

	mv build/envs.txt.tmp build/envs.txt;


build/deps.txt: build/envs.txt requirements/*.txt
	@mkdir -p build/;

	@SUPPORTED_PYTHON_VERSIONS="$(SUPPORTED_PYTHON_VERSIONS)" \
		VENV_NAMES="$(VENV_NAMES)" \
		VENV_PATHS="$(VENV_PATHS)" \
		VENV_PYTHON_PATHS="$(VENV_PYTHON_PATHS)" \
		bash scripts/update_venv_deps.sh;

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

	@for env_py in $(VENV_PYTHON_PATHS); do \
		printf "\n# pip freeze for $${env_py}:\n" >> build/deps.txt.tmp; \
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
			} else if ($$0 ~ /^[a-zA-Z\-\_0-9.\/]+:/) { \
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
		Makefile.bootstrapit.make Makefile

	@if [[ ! -f $(DEV_ENV_PY) ]]; then \
	echo "Missing python interpreter at $(DEV_ENV_PY) !"; \
	echo "You problably want to first setup the virtual environments:"; \
	echo ""; \
	echo "    make conda"; \
	echo ""; \
	exit 0; \
	fi

	@if [[ ! -f $(CONDA_BIN) ]]; then \
	echo "No conda installation found!"; \
	echo "You problably want to first setup the virtual environments:"; \
	echo ""; \
	echo "    make conda"; \
	echo ""; \
	exit 0; \
	fi


## Full help message for each task.
.PHONY: helpverbose
helpverbose:
	@printf "Available make targets for \033[97m$(PKG_NAME)\033[0m:\n";

	@awk '{ \
			if ($$0 ~ /^.PHONY: [a-zA-Z\-\_0-9]+$$/) { \
				helpCommand = substr($$0, index($$0, ":") + 2); \
				if (helpMessage) { \
					printf "\033[36m%-20s\033[0m %s\n", \
						helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^[a-zA-Z\-\_0-9.\/]+:/) { \
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
		Makefile.bootstrapit.make Makefile


## -- Project Setup --


## Delete conda envs and cache 💩
.PHONY: clean
clean:
	@for env_name in $(VENV_NAMES); do \
		env_py="$(VENVS_ROOT)/$${env_name}/bin/python"; \
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
	@printf "\n    make clean completed  🧹🧹🧹 \n\n"


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


## Create/Update python virtual environments
.PHONY: venvs
venvs: build/deps.txt


## Install git pre-push hooks
.PHONY: git_hooks
git_hooks:
	@rm -f "$(PWD)/.git/hooks/pre-push"
	ln -s "$(PWD)/scripts/pre-push-hook.sh" "$(PWD)/.git/hooks/pre-push"


## -- Integration --


## Run isort with --check-only
.PHONY: lint_isort
lint_isort:
	@printf "isort ...\n"
	@$(DEV_ENV)/bin/isort \
		--check-only \
		--line-width=$(MAX_LINE_LEN) \
		--project $(MODULE_NAME) \
		src/ test/
	@printf "\e[1F\e[9C ok\n"


## Run sjfmt with --check
.PHONY: lint_fmt
lint_fmt:
	@printf "sjfmt ...\n"
	@$(DEV_ENV)/bin/sjfmt \
		--target-version=py36 \
		--skip-string-normalization \
		--line-length=$(MAX_LINE_LEN) \
		--check \
		src/ test/ 2>&1 | sed "/All done/d" | sed "/left unchanged/d"
	@printf "\e[1F\e[9C ok\n"


## Run flake8
.PHONY: lint_flake8
lint_flake8:
	@rm -f reports/flake8*;
	@mkdir -p "reports/";

	@printf "flake8 ..\n"
	@$(DEV_ENV)/bin/flake8 src/ --tee --output-file reports/flake8.txt || exit 0;
	@$(DEV_ENV)/bin/flake8_junit reports/flake8.txt reports/flake8.xml >> /dev/null;
	@$(DEV_ENV_PY) scripts/exit_0_if_empty.py reports/flake8.txt;

	@printf "\e[1F\e[9C ok\n"


## Run pylint --errors-only.
.PHONY: lint_pylint_errors
lint_pylint_errors:
	@printf "pylint ..\n";
	@$(DEV_ENV)/bin/pylint --errors-only --jobs=4 --rcfile=setup.cfg \
		src/ test/
	@printf "\e[1F\e[9C ok\n"


## Run pylint.
.PHONY: lint_pylint
lint_pylint:
	@mkdir -p "reports/";

	@printf "pylint ..\n";
	@$(DEV_ENV)/bin/pylint-ignore --rcfile=setup.cfg \
		src/ test/
	@printf "\e[1F\e[9C ok\n"


## Run pylint-ignore --update-ignorefile.
.PHONY: pylint_ignore
pylint_ignore:
	$(DEV_ENV)/bin/pylint-ignore --rcfile=setup.cfg \
		src/ test/ --update-ignorefile


## Run flake8 linter and check for fmt
.PHONY: lint
lint: lint_isort lint_fmt lint_flake8 lint_pylint


## Run mypy type checker
.PHONY: mypy
mypy:
	@rm -rf ".mypy_cache";
	@rm -rf "reports/mypycov";
	@mkdir -p "reports/";

	@printf "mypy ....\n"
	@MYPYPATH=stubs/:vendor/ $(DEV_ENV_PY) -m mypy \
		--html-report reports/mypycov \
		--no-error-summary \
		src/ | sed "/Generated HTML report/d"
	@printf "\e[1F\e[9C ok\n"


## Run pytest unit and integration tests
.PHONY: test
test:
	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";
	@rm -rf "reports/testcov/";
	@rm -f "reports/pytest*";
	@mkdir -p "reports/";

	# First we test the local source tree using the dev environment
	ENV=$${ENV-dev} \
		PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		PATH=$(DEV_ENV)/bin:$$PATH \
		$(DEV_ENV_PY) -m pytest -v \
		--doctest-modules \
		--verbose \
		--cov-report "html:reports/testcov/" \
		--cov-report term \
		--html=reports/pytest/index.html \
		--junitxml reports/pytest.xml \
		-k "$${PYTEST_FILTER-$${FLTR}}" \
		$(shell cd src/ && ls -1 */__init__.py | awk '{ sub(/\/__init__.py/, "", $$1); print "--cov "$$1 }') \
		test/ src/;

	# Next we install the package and run the test suite against it.

	# 	IFS=' ' read -r -a env_py_paths <<< "$(VENV_PYTHON_PATHS)"; \
	# 	for i in $${!env_py_paths[@]}; do \
	# 		env_py=$${env_py_paths[i]}; \
	# 		$${env_py} -m pip install --upgrade .; \
	# 		PYTHONPATH="" ENV=$${ENV-dev} $${env_py} -m pytest test/; \
	# 	done;

	@rm -rf ".pytest_cache";
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";


## Run import sorting on src/ and test/
.PHONY: fmt_isort
fmt_isort:
	@$(DEV_ENV)/bin/isort \
		--line-width=$(MAX_LINE_LEN) \
		--project $(MODULE_NAME) \
		src/ test/;


## Run code formatter on src/ and test/
.PHONY: fmt_sjfmt
fmt_sjfmt:
	@$(DEV_ENV)/bin/sjfmt \
		--target-version=py36 \
		--skip-string-normalization \
		--line-length=$(MAX_LINE_LEN) \
		src/ test/;


## Run code formatters
.PHONY: fmt
fmt: fmt_isort fmt_sjfmt


## -- Helpers --


## Shortcut for make fmt lint mypy devtest test
.PHONY: check
check: fmt lint mypy devtest test


## Start subshell with environ variables set.
.PHONY: env_subshell
env_subshell:
	@bash --init-file <(echo '\
		source $(HOME)/.bashrc; \
		export PYTHONPATH="src/:vendor/:$$PYTHONPATH"; \
		source $(DEV_ENV_NAME)/bin/activate \
	')


## Usage: "source ./activate", to deactivate: "deactivate"
.PHONY: activate
activate:
	@echo 'source $(VENVS_ROOT)/etc/profile.d/conda.sh;'
	@echo 'if [[ -z $$ENV ]]; then'
	@echo '		export _env_before_activate=$${ENV};'
	@echo 'fi'
	@echo 'if [[ -z $$PYTHONPATH ]]; then'
	@echo '		export _pythonpath_before_activate=$${PYTHONPATH};'
	@echo 'fi'
	@echo 'export ENV=$${ENV-dev};'
	@echo 'export PYTHONPATH="src/:vendor/:$$PYTHONPATH";'
	@echo 'source $(DEV_ENV_NAME)/bin/activate;'

	@echo 'function deactivate {'
	@echo '		if [[ -z $${_env_before_activate} ]]; then'
	@echo '				export ENV=$${_env_before_activate}; '
	@echo '		else'
	@echo '				unset ENV;'
	@echo '		fi'
	@echo '		if [[ -z $${_pythonpath_before_activate} ]]; then'
	@echo '				export PYTHONPATH=$${_pythonpath_before_activate}; '
	@echo '		else'
	@echo '				unset PYTHONPATH;'
	@echo '		fi'
	@echo '		unset _env_before_activate;'
	@echo '		unset _pythonpath_before_activate;'
	@echo '		conda deactivate;'
	@echo '};'


## Drop into an ipython shell with correct env variables set
.PHONY: ipy
ipy:
	@ENV=$${ENV-dev} \
		PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		PATH=$(DEV_ENV)/bin:$$PATH \
		$(DEV_ENV)/bin/ipython


## Like `make test`, but with debug parameters
.PHONY: devtest
devtest:
	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";

	ENV=$${ENV-dev} \
		PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		PATH=$(DEV_ENV)/bin:$$PATH \
		$(DEV_ENV_PY) -m pytest -v \
		--doctest-modules \
		--no-cov \
		--durations 5 \
		--verbose \
		--capture=no \
		--exitfirst \
		--failed-first \
		-k "$${PYTEST_FILTER-$${FLTR}}" \
		test/ src/;

	@rm -rf "src/__pycache__";
	@rm -rf "test/__pycache__";


## Run `make lint mypy test` using docker
.PHONY: citest
citest:
	$(DOCKER) build --file Dockerfile --tag tmp_citest_$(PKG_NAME) .
	$(DOCKER) run --tty tmp_citest_$(PKG_NAME) make lint mypy test test_compat


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
	$(DEV_ENV)/bin/bumpver update;


## Create python sdist and bdist_wheel files
.PHONY: dist_build
dist_build:
	@rm -rf build/lib3to6_out/
	@rm -rf build/lib/
	@rm -rf build/bdist*
	$(DEV_ENV_PY) setup.py sdist;
	$(DEV_ENV_PY) setup.py bdist_wheel --python-tag=$(BDIST_WHEEL_PYTHON_TAG);
	@rm -rf src/*.egg-info


## Upload sdist and bdist files to pypi
.PHONY: dist_upload
dist_upload:
	@if [[ "1" != "1" ]]; then \
		echo "FAILSAFE! Not publishing a private package."; \
		echo "  To avoid this set IS_PUBLIC=1 in bootstrap.sh and run it."; \
		exit 1; \
	fi

	$(DEV_ENV)/bin/twine check $$($(SDIST_FILE_CMD));
	$(DEV_ENV)/bin/twine check $$($(BDIST_WHEEL_FILE_CMD));
	$(DEV_ENV)/bin/twine upload --skip-existing \
		--repository pypi-legacy \
		$$($(SDIST_FILE_CMD)) $$($(BDIST_WHEEL_FILE_CMD));


## bump_version dist_build dist_upload
.PHONY: dist_publish
dist_publish: bump_version dist_build dist_upload


## Build docker images. Must be run when dependencies are added
##   or updated. The main reasons this can fail are:
##   1. No ssh key at $(HOME)/.ssh/$(PKG_NAME)_gitlab_runner_id_rsa
##      (which is needed to install packages from private repos
##      and is copied into a temp container during the build).
##   2. Your docker daemon is not running
##   3. You're using WSL and docker is not exposed on tcp://localhost:2375
##   4. You're using WSL but didn't do export DOCKER_HOST="tcp://localhost:2375"
.PHONY: docker_build
docker_build:
	$(DOCKER) build \
		--file docker_base.Dockerfile \
		--tag $(DOCKER_BASE_IMAGE):$(DOCKER_IMAGE_VERSION) \
		--tag $(DOCKER_BASE_IMAGE) \
		.;

	$(DOCKER) push $(DOCKER_BASE_IMAGE)
