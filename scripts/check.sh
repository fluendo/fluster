#!/bin/bash

readonly root=$(git rev-parse --show-toplevel)

echo "Checking style with autopep8..."
find $root -iname '*.py' | parallel autopep8 -i

echo "Running pylint..."
find $root -iname '*.py' | parallel pylint -E

echo "Running dummy test..."
$root/fluxion_test.py run -ts dummy
