#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

time=$(date +%Y-%m-%d_%H-%M-%S)
fname=$SCRIPT_DIR/$time.bundle

echo Creating bundle: $fname
git bundle create $fname --all
