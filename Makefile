.PHONY: default all py-tests go-tests pycoverage gocoverage cli-sandbox

default: all

all: pycoverage gocoverage

py-tests:
	cd ./sdk/py && pytest

pycoverage:
	cd ./sdk/py && coverage run -m pytest && coverage report

go-tests:
	cd ./cli/src && go test ./core

gocoverage:
	cd ./cli/src && go test -coverprofile=coverage.out ./core && go tool cover -func=coverage.out

cli-sandbox:
	docker-compose -f test_env/docker-compose.yml build
	docker-compose -f test_env/docker-compose.yml run --rm --name sb-cli-dev sb-cli-dev
