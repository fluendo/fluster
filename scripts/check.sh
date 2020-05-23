#!/bin/bash

readonly root=$(git rev-parse --show-toplevel)

echo "Checking style with autopep8..."
find $root -iname '*.py' | xargs autopep8 -i --ignore E402

echo "Running pylint..."
pylint -E $root/fluxion/
pylint -E $root/fluxion.py
PYTHONPATH=$root pylint -E $root/scripts/

echo "Running dummy test..."
$root/fluxion.py run -ts dummy
