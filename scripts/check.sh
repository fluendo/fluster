#!/bin/bash

readonly root="$(realpath $( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )/..)"

find $root -iname '*.py' | parallel autopep8 -i
find $root -iname '*.py' | parallel pylint -E
