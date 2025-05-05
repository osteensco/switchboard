.PHONY: default all py

default: all

all: py

py:
	cd ./sdk/py && pytest
