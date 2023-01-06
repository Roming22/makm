#!/bin/bash -e
SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"
poetry run python -m cProfile -s cumulative -o profile.state "$SCRIPT_DIR/../myapp/main.py" "$@"