#!/usr/bin/env bash

set -e

: "${PYTHON_TAG:=3.8}"
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
    python:"${PYTHON_TAG}" \
    /bin/bash -c "cd /app && pip install --quiet -U .[tests] && pytest ${PYTEST_ARGS}" || PYTEST_EXIT_CODE=$?

set +x

docker volume rm "${VOL_NAME}"

exit "${PYTEST_EXIT_CODE}"
