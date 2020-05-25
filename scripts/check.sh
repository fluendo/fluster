#!/bin/bash

readonly root=$(git rev-parse --show-toplevel)

make -C $root check
