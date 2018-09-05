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

BDIST_WHEEL_PYCALVER = $(shell bash -c "ls -1t dist/pycalver*py2*.whl | head -n 1")
SDIST_PYCALVER = $(shell bash -c "ls -1t dist/pycalver*.tar.gz | head -n 1")
BUILD_LOG_DIR = "test_build_logs/"
BUILD_LOG_FILE := $(shell date +"$(BUILD_LOG_DIR)%Y%m%dt%H%M%S%N.log")


build/.install.make_marker: setup.py build/envs.txt requirements*.txt
	$(PYTHON37) -m pip install --upgrade --quiet $$(cat requirements.txt);
	$(PYTHON36) -m pip install --upgrade --quiet $$(cat requirements.txt);
	$(PYTHON27) -m pip install --upgrade --quiet $$(cat requirements.txt);

	$(PYTHON37) -m pip install --upgrade \
		$$(cat requirements-test.txt) \
		$$(cat requirements-dev.txt);

	# NOTE (mb 2018-08-23): The linter has an issue running with
	# 	python 3.7 because some code in pycodestyle=2.3.1
	#	but we have to wait for a flake8 update because
	#	reasons... https://github.com/PyCQA/pycodestyle/issues/728
	@mkdir -p lib/
	$(PYTHON37) -m pip install --src lib/ \
		-e "git+https://gitlab.com/pycqa/flake8@master#egg=flake8";

	@mkdir -p build/
	@touch build/.install.make_marker


clean:
	rm -f build/envs.txt
	rm -f build/.setup_conda_envs.make_marker
	rm -f build/.install.make_marker


lint: build/.install.make_marker
	@echo -n "lint.."
	@$(PYENV37)/bin/flake8 src/pycalver/
	@echo "ok"


mypy: build/.install.make_marker
	@echo -n "mypy.."
	@MYPYPATH=stubs/ $(PYTHON37) -m mypy \
		src/pycalver/
	@echo "ok"


test: build/.install.make_marker
	@PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest \
		--cov-report html \
		--cov=pycalver \
		test/


devtest: build/.install.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest -v \
		--cov-report term \
		--cov=pycalver \
		--capture=no \
		--exitfirst \
		test/


build/README.html: build/.install.make_marker README.rst CHANGELOG.rst
	@cat README.rst > build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CHANGELOG.rst >> build/.full_readme.rst
	@$(PYENV37)/bin/rst2html5 --strict \
		build/.full_readme.rst > build/README.html.tmp
	@mv build/README.html.tmp build/README.html
	@echo "updated build/README.html"


readme: build/README.html


build/.src_files.txt: setup.py build/envs.txt src/pycalver/*.py
	@mkdir -p build/
	@ls -l setup.py build/envs.txt src/pycalver/*.py > build/.src_files.txt.tmp
	@mv build/.src_files.txt.tmp build/.src_files.txt


rm_site_packages:
	# whackamole
	rm -rf $(PYENV37)/lib/python3.6/site-packages/pycalver/
	rm -rf $(PYENV37)/lib/python3.6/site-packages/pycalver*.dist-info/
	rm -rf $(PYENV37)/lib/python3.6/site-packages/pycalver*.egg-info/
	rm -f $(PYENV37)/lib/python3.6/site-packages/pycalver*.egg


build/.local_install.make_marker: build/.src_files.txt rm_site_packages
	@echo "installing pycalver.."
	@$(PYTHON37) setup.py install --no-compile --verbose
	@mkdir -p build/
	@$(PYTHON37) -c "import pycalver"
	@echo "install completed for pycalver"
	@touch build/.local_install.make_marker


build: build/.local_install.make_marker
	@mkdir -p $(BUILD_LOG_DIR)
	@echo "writing full build log to $(BUILD_LOG_FILE)"
	@echo "building pycalver.."
	@$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG_FILE)
	@echo "build completed for pycalver"


upload: build/.install.make_marker build/README.html
	$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3
	$(PYENV37)/bin/twine upload $(BDIST_WHEEL_PYCALVER)


setup_conda_envs: build/.setup_conda_envs.make_marker

install: build/.install.make_marker

run_main:
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON37) -m pycalver --help
