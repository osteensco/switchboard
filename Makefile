.PHONY: default all py

default: all

all: py

py:
	cd py && pytest
