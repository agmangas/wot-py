#!/usr/bin/env bash

set -x

: ${PYTEST_ARGS:="-v --disable-warnings"}

PYTHON_TAG="2.7" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_27=$?

PYTHON_TAG="3.6" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_36=$?

PYTHON_TAG="3.7" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_37=$?

PYTHON_TAG="3.8" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_38=$?

PYTHON_TAG="3.9" PYTEST_ARGS=${PYTEST_ARGS} ./pytest-docker.sh
EXIT_39=$?

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

print_section "Python 2.7" $EXIT_27
print_section "Python 3.6" $EXIT_36
print_section "Python 3.7" $EXIT_37
print_section "Python 3.8" $EXIT_38
print_section "Python 3.9" $EXIT_39