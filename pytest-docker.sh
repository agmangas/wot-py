#!/usr/bin/env bash

set -e
set -x

: ${PYTHON_TAG:="3.8"}
: ${PYTEST_ARGS:="-v"}

CURR_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
TEMP_BASE=$(python3 -c "import tempfile; print(tempfile.gettempdir());")
TEMP_NAME=$(python3 -c "import uuid; print(\"wotpy-{}\".format(uuid.uuid4().hex));")
TEMP_PATH=${TEMP_BASE}/${TEMP_NAME}

rm -fr ${TEMP_PATH}
cp -r ${CURR_DIR} ${TEMP_PATH}
cd ${TEMP_PATH}
git clean -x -d -f

PYTEST_EXIT_CODE=0

docker run --rm -it \
-v $(pwd):/app \
-e WOTPY_TESTS_MQTT_BROKER_URL=${WOTPY_TESTS_MQTT_BROKER_URL} \
python:${PYTHON_TAG} \
/bin/bash -c "cd /app && pip install -U .[tests] && pytest ${PYTEST_ARGS}" || PYTEST_EXIT_CODE=$?

cd ${CURR_DIR}
rm -fr ${TEMP_PATH}

exit $PYTEST_EXIT_CODE