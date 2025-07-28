.PHONY: default all py pycoverage

default: all

all: pycoverage

py:
	cd ./sdk/py && pytest

pycoverage:
	cd ./sdk/py && coverage run -m pytest && coverage report
