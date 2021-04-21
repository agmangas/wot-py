#!/usr/bin/env bash

set -e
set -x

: ${TEMP_NAME:="wotpytest"}
: ${PYTHON_TAG:="3.8"}
: ${PYTEST_ARGS:=""}

CURR_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
TEMP_DIR=$(python -c "import tempfile; print(tempfile.gettempdir());")

rm -fr ${TEMP_DIR}/${TEMP_NAME}
cp -r ${CURR_DIR} ${TEMP_DIR}/${TEMP_NAME}
cd ${TEMP_DIR}/${TEMP_NAME}
git clean -x -d -f

docker run --rm -it \
-v $(pwd):/app \
-e WOTPY_TESTS_MQTT_BROKER_URL=${WOTPY_TESTS_MQTT_BROKER_URL} \
python:${PYTHON_TAG} \
/bin/bash -c "cd /app && pip install -U .[tests] && pytest -v ${PYTEST_ARGS}"

cd ${CURR_DIR}
rm -fr ${TEMP_DIR}/${TEMP_NAME}
