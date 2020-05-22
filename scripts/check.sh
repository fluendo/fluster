#!/bin/bash

readonly root=$(git rev-parse --show-toplevel)

echo "Checking style with autopep8..."
find $root -iname '*.py' | xargs autopep8 -i --ignore E402

echo "Running pylint..."
find $root -iname '*.py' | xargs pylint -E

echo "Running dummy test..."
$root/fluxion_test.py run -ts dummy