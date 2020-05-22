#!/bin/bash

readonly dir="$( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"

readonly find_cmd="find $dir/.. -iname "*.py""

$find_cmd | parallel autopep8 -i
$find_cmd | parallel pylint -E
