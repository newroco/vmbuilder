#!/usr/bin/make -f

test:
	@echo Running unittests...
	@nosetests

coverage:
	@nosetests --quiet --with-coverage --cover-package VMBuilder

report:
	@nosetests --quiet --with-coverage --cover-package VMBuilder --cover-html --cover-html-dir coverage-report

clean:
	rm -rf .coverage coverage-report
