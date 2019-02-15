

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


CONDA_ENV_PYS := \
	$(shell echo "$(CONDA_ENV_PATHS)" \
	| sed 's!\(_py[[:digit:]]\+\)!\1/bin/python!g' \
	| sed 's!\(_pypy2[[:digit:]]\)!\1/bin/pypy!g' \
	| sed 's!\(_pypy3[[:digit:]]\)!\1/bin/pypy3!g' \
)


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

	IFS=' ' read -r -a env_pys <<< "$(CONDA_ENV_PYS)"; \
	for i in $${!env_pys[@]}; do \
		env_py=$${env_pys[i]}; \
		$${env_py} -m pip install --upgrade build/test_wheel/*.whl; \
		PYTHONPATH="" ENV=$${ENV-dev} \
			$${env_py} -m pytest --verbose compat_test/; \
	done;
