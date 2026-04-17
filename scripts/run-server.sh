#!/bin/bash


SCRIPT_DIR=$(dirname "$(realpath "$0")")
CODE_DIR=$(dirname "${SCRIPT_DIR}")/app
PARENT_DIR=$(dirname "${CODE_DIR}")
export PYTHONPATH=$PYTHONPATH:"${PARENT_DIR}"

echo "${CODE_DIR}"


REQ_FP="${PARENT_DIR}/requirements.txt"
echo "Installing requirements from ${REQ_FP} ..."
pip install -r "${REQ_FP}"

echo "Running api server for evaluation on port 8000"
uvicorn api.endpoints:app --reload --host 0.0.0.0 --port 8000