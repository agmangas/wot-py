#!/usr/bin/env bash

set -e
set -x

pip3 install --upgrade pip
pip3 install -U -e .[tests]