#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> API: sync, lint, format, typecheck, test"
cd "$root/apps/api"
python -m uv sync --group dev
python -m uv run ruff check .
python -m uv run ruff format --check .
python -m uv run pyright
python -m uv run pytest

echo "==> Web: install, lint, typecheck, test"
cd "$root/apps/web"
npm ci
npm run lint
npm run typecheck
npm test

echo "==> Docker Compose file is valid"
cd "$root"
docker compose config >/dev/null

echo "All documented checks passed."
