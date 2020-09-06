
PACKAGE_NAME := pycalver

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.8

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# Some valid options are:
# - python=2.7
# - python=3.5
# - python=3.6
# - python=3.7
# - pypy2.7
# - pypy3.5
SUPPORTED_PYTHON_VERSIONS := python=2.7 python=3.5 python=3.6 python=3.8 pypy2.7 pypy3.5


include makefile.bootstrapit.make

## -- Extra/Custom/Project Specific Tasks --


## Start the development http server in debug mode
##    This is just to illustrate how to add your
##    extra targets outside of the main makefile.
.PHONY: serve
serve:
	echo "Not Implemented"


COMPAT_TEST_FILES = $(shell ls -1 test/*.py 2>/dev/null | awk '{ printf " compat_"$$0 }')

compat_test/%.py: test/%.py
	@mkdir -p compat_test/;
	$(DEV_ENV)/bin/lib3to6 $< > $@.tmp;
	mv $@.tmp $@;


## Run pytest integration tests
.PHONY: test_compat
test_compat: $(COMPAT_TEST_FILES)
	rm -rf compat_test/fixtures;
	mkdir -p compat_test/fixtures;
	cp -R test/fixtures compat_test/

	# install the package and run the test suite against it.
	rm -rf build/test_wheel;
	mkdir -p build/test_wheel;
	$(DEV_ENV_PY) setup.py bdist_wheel --dist-dir build/test_wheel;

	IFS=' ' read -r -a env_pys <<< "$(CONDA_ENV_BIN_PYTHON_PATHS)"; \
	for i in $${!env_pys[@]}; do \
		env_py=$${env_pys[i]}; \
		$${env_py} -m pip install --upgrade build/test_wheel/*.whl; \
		ENABLE_BACKTRACE=0 PYTHONPATH="" ENV=$${ENV-dev} \
			$${env_py} -m pytest --verbose compat_test/; \
	done;

	rm -rf compat_test/
