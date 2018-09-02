.PHONY: setup_conda_envs install \
	test lint \
	clean rm_site_packages \
	build readme upload


build/.setup_conda_envs.make_marker:
	conda create --name pycalver_37 python=3.7 --yes
	conda create --name pycalver_36 python=3.6 --yes
	conda create --name pycalver_27 python=2.7 --yes
	@mkdir -p build/
	@touch build/.setup_conda_envs.make_marker


build/envs.txt: build/.setup_conda_envs.make_marker
	@mkdir -p build/
	conda env list | grep pycalver | rev | cut -d " " -f1 | rev > build/envs.txt.tmp
	mv build/envs.txt.tmp build/envs.txt


PYENV37 ?= $(shell bash -c "grep 37 build/envs.txt || true")
PYENV36 ?= $(shell bash -c "grep 36 build/envs.txt || true")
PYENV27 ?= $(shell bash -c "grep 27 build/envs.txt || true")
PYTHON37 ?= $(PYENV37)/bin/python
PYTHON36 ?= $(PYENV36)/bin/python
PYTHON27 ?= $(PYENV27)/bin/python

BDIST_WHEEL_LIB3TO6 = $(shell bash -c "ls -1t dist/pycalver*py2*.whl | head -n 1")
SDIST_LIB3TO6 = $(shell bash -c "ls -1t dist/pycalver*.tar.gz | head -n 1")
DIST_WHEEL_TEST = $(shell bash -c "ls -1t test_project/dist/*py2*.whl | head -n 1")
BUILD_LOG_DIR = "test_build_logs/"
BUILD_LOG_FILE := $(shell date +"$(BUILD_LOG_DIR)%Y%m%dt%H%M%S%N.log")


build/.install.make_marker: setup.py build/envs.txt
	$(PYTHON36) -m pip install --upgrade --quiet \
		pip setuptools wheel twine \
		flake8 mypy typing-extensions \
		rst2html5 \
		pytest pytest-cov \
		ipython pudb \
		pathlib2 click;

	$(PYTHON37) -m pip install --upgrade --quiet pip setuptools wheel;
	$(PYTHON36) -m pip install --upgrade --quiet pip setuptools wheel;
	$(PYTHON27) -m pip install --upgrade --quiet pip setuptools wheel;

	@mkdir -p build/
	@touch build/.install.make_marker


clean:
	rm -f build/envs.txt
	rm -f build/.setup_conda_envs.make_marker
	rm -f build/.install.make_marker


# NOTE (mb 2018-08-23): The linter has an issue running with
# 	python 3.7 because some code in pycodestyle=2.3.1
#	but we have to wait for a flake8 update because
#	reasons... https://github.com/PyCQA/pycodestyle/issues/728


lint: build/.install.make_marker
	@echo -n "lint.."
	@$(PYTHON36) -m flake8 src/pycalver/
	@echo "ok"


mypy: build/.install.make_marker
	@echo -n "mypy.."
	@MYPYPATH=stubs/ $(PYTHON36) -m mypy \
		src/pycalver/
	@echo "ok"


test: build/.install.make_marker
	@PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest \
		--cov-report html \
		--cov=pycalver \
		test/


devtest: build/.install.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest -v \
		--cov-report term \
		--cov=pycalver \
		--capture=no \
		--exitfirst \
		test/


build/.coverage_percent.txt: test
	@mkdir -p build/
	@grep -oP '>[0-9]+%</td>' htmlcov/index.html \
		| head -n 1 \
		| grep -oP '[.0-9]+' \
		> build/.coverage_percent.txt


README.rst: build/.coverage_percent.txt
	@sed -i "s/coverage-[0-9]*/coverage-$$(cat build/.coverage_percent.txt)/" README.rst


build/README.html: build/.install.make_marker README.rst CHANGELOG.rst
	@cat README.rst > build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CHANGELOG.rst >> build/.full_readme.rst
	@$(PYENV36)/bin/rst2html5 --strict \
		build/.full_readme.rst > build/README.html.tmp
	@mv build/README.html.tmp build/README.html
	@echo "updated build/README.html"


readme: build/README.html


build/.src_files.txt: setup.py build/envs.txt src/pycalver/*.py
	@mkdir -p build/
	@ls -l setup.py build/envs.txt src/pycalver/*.py > build/.src_files.txt.tmp
	@mv build/.src_files.txt.tmp build/.src_files.txt


rm_site_packages:
	rm -rf $(PYENV36)/lib/python3.6/site-packages/pycalver/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/pycalver*.dist-info/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/pycalver*.egg-info/
	rm -f $(PYENV36)/lib/python3.6/site-packages/pycalver*.egg


build/.local_install.make_marker: build/.src_files.txt rm_site_packages
	@echo "installing pycalver.."
	@$(PYTHON36) setup.py install --no-compile --verbose
	@mkdir -p build/
	@$(PYTHON36) -c "import pycalver"
	@echo "install completed for pycalver"
	@touch build/.local_install.make_marker


build: build/.local_install.make_marker
	@mkdir -p $(BUILD_LOG_DIR)
	@echo "writing full build log to $(BUILD_LOG_FILE)"
	@echo "building pycalver.."
	@$(PYTHON36) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG_FILE)
	@echo "build completed for pycalver"


upload: build/.install.make_marker build/README.html
	$(PYTHON36) setup.py bdist_wheel --python-tag=py2.py3
	$(PYENV36)/bin/twine upload $(BDIST_WHEEL_LIB3TO6)


setup_conda_envs: build/.setup_conda_envs.make_marker

install: build/.install.make_marker

run_main:
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON36) -m pycalver --help
