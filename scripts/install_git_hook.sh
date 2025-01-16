#!/bin/bash

readonly root=$(git rev-parse --show-toplevel)

cp $root/scripts/check.sh $root/.git/hooks/pre-commit
pre-commit install
