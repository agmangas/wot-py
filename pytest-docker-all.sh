#!/usr/bin/env bash

set -x

: ${PYTEST_ARGS:="-v --disable-warnings"}

PYTHON_TAG="2.7" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
PYTHON_TAG="3.6" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
PYTHON_TAG="3.7" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
PYTHON_TAG="3.8" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
PYTHON_TAG="3.9" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh