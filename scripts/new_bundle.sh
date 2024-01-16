#!/usr/bin/env bash

REPO=$(git rev-parse --show-toplevel)
BUNDLES=$REPO/bundles

mkdir -p $BUNDLES

fname=$BUNDLES/$(date +%Y-%m-%d_%H-%M-%S).bundle

echo Creating bundle: $fname
git bundle create $fname --all
