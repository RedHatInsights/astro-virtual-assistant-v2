#
# Targets for validation and test tools
#

include scripts/make/Makefile.variables.mk

PYTEST_FLAGS =

test: test-python

test-python-update-snapshot: PYTEST_FLAGS+= --snapshot-update
test-python-update-snapshot: test-python

test-python:
	uv run --directory libs/common pytest $(PYTEST_FLAGS)
	uv run --directory services/virtual-assistant pytest $(PYTEST_FLAGS)
	uv run --directory services/watson-extension pytest $(PYTEST_FLAGS)

test-python-coverage:
	uv run --directory libs/common coverage run -m pytest --junitxml=junit.xml -o junit_family=legacy && uv run --directory libs/common coverage report
	uv run --directory services/virtual-assistant coverage run -m pytest --junitxml=junit.xml && uv run --directory services/virtual-assistant coverage report
	uv run --directory services/watson-extension coverage run -m pytest --junitxml=junit.xml && uv run --directory services/watson-extension coverage report
	uv run coverage combine libs/common/.coverage services/virtual-assistant/.coverage services/watson-extension/.coverage
	if [ $(COVERAGE_FORMAT) ]; then uv run coverage $(COVERAGE_FORMAT); fi

test-python-coverage-html: COVERAGE_FORMAT = "html"
test-python-coverage-html: test-python-coverage

test-openapi:
	curl -X GET http://0.0.0.0:5005/api/virtual-assistant/v1/openapi.json
