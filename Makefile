.PHONY: default all py pycoverage gocoverage

default: all

all: pycoverage gocoverage

py_tests:
	cd ./sdk/py && pytest

pycoverage:
	cd ./sdk/py && coverage run -m pytest && coverage report

go_tests:
	cd ./cli/src && go test ./core

gocoverage:
	cd ./cli/src && go test -coverprofile=coverage.out ./core && go tool cover -func=coverage.out
