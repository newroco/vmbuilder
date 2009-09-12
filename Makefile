#!/usr/bin/make -f

test: clean stamp
	@nosetests --verbose

stamp:
	@touch $@

build:
	@python setup.py bdist_egg sdist

coverage:
	@nosetests --quiet --with-coverage --cover-package VMBuilder

report:
	@nosetests --quiet --with-coverage --cover-package VMBuilder --cover-html --cover-html-dir coverage-report

clean:
	@rm -rf stamp .coverage coverage-report
