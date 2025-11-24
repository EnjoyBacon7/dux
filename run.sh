#!/bin/bash

export UPLOAD_DIR="${UPLOAD_DIR:-./uploads}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

uv run uvicorn server.app:app --reload --host "$HOST" --port "$PORT"
