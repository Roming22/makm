#!/bin/bash -e
SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"

PYTHON="python3"
if command -v pypy3; then
    PYTHON="pypy3"
fi

BIN=()
case "$1" in
    -p|--profile)
        BIN=( "-m" "cProfile" "-s" "cumulative" "-o" "profile.state")
        PROFILE="1"
        shift
        ;;
esac

poetry run "$PYTHON" "${BIN[@]}" "$SCRIPT_DIR/../myapp/main.py" "$@"

if [ -n "$PROFILE" ]; then
    timeout 30 snakeviz profile.state &
    sleep 3
fi