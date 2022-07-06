#!/usr/bin/env bash

: ${PYTEST_ARGS:=" "}

set -x

PYTHON_TAG="3.7" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_37=$?

PYTHON_TAG="3.8" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_38=$?

PYTHON_TAG="3.9" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_39=$?

PYTHON_TAG="3.10" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_310=$?

set +x

RED='\033[0;31m'
GREEN='\033[0;32m'
RESET='\033[0m'

print_section () {
    if [[ $2 != 0 ]]
    then
        echo -e "$1 :: ${RED}Error${RESET}"
    else
        echo -e "$1 :: ${GREEN}OK${RESET}"
    fi
}

print_section "Python 3.7" $EXIT_37
print_section "Python 3.8" $EXIT_38
print_section "Python 3.9" $EXIT_39
print_section "Python 3.10" $EXIT_310