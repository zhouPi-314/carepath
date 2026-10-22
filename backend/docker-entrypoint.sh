#!/bin/sh
set -eu

alembic upgrade head

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m carepath.seed
fi

exec uvicorn carepath.main:app --host 0.0.0.0 --port 8000
