#!/usr/bin/env bash

# Copyright (c) 2021 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

set -e

: "${PYTHON_TAG:='3.10'}"
: "${PYTEST_ARGS:=-v}"

echo "Running python tests for version ${PYTHON_TAG} with arguments \"${PYTEST_ARGS}\""

CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

echo "Creating temporary container volume"
VOL_NAME=$(python3 -c "import uuid; print(\"wotpy_tests_{}\".format(uuid.uuid4().hex));")

docker volume create "${VOL_NAME}"

docker run --rm -it \
    -v "${VOL_NAME}":/vol \
    -v "${CURR_DIR}":/src \
    alpine \
    sh -c "rm -fr /vol/{*,.*} && cp -a /src/. /vol/"

PYTEST_EXIT_CODE=0

echo "Running test container. Environment setup will take a while."

set -x

docker run --rm -it \
    -v "${VOL_NAME}":/app \
    -e WOTPY_TESTS_MQTT_BROKER_URL="${WOTPY_TESTS_MQTT_BROKER_URL}" \
    -e WOTPY_TESTS_ZENOH_ROUTER_URL="${WOTPY_TESTS_ZENOH_ROUTER_URL}" \
    python:"${PYTHON_TAG}" \
    /bin/bash -c "cd /app && pip install --quiet -U .[tests] && pytest ${PYTEST_ARGS}" || PYTEST_EXIT_CODE=$?

set +x

docker volume rm "${VOL_NAME}"

exit "${PYTEST_EXIT_CODE}"
