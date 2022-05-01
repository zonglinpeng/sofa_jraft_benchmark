#!/usr/bin/env bash

set -o errexit
set -o xtrace
set -o pipefail

# Maven package first

if ! [ -x "$(command -v docker)" ]; then
    printf "%s\n" 'Error: docker is not installed.' >&2
    exit 1
fi

if ! [ -x "$(command -v git)" ]; then
    printf "%s\n" 'Error: git is not installed.' >&2
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel)

# docker image rm "raft:dev"

docker buildx build "${PROJECT_ROOT}/raft/sofa-jraft/jraft-example/target/jraft-bin" -f "${PROJECT_ROOT}/raft/docker/Dockerfile" -t zonglin7/raft:dev