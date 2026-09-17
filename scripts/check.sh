#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> API: sync, lint, format, typecheck, test"
cd "$root/apps/api"
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest

echo "==> Web: install, lint, typecheck, test, build"
cd "$root/apps/web"
npm ci
npm run lint
npm run typecheck
npm test
npm run build

echo "==> Docker Compose file is valid"
cd "$root"
docker compose config >/dev/null

echo "All documented checks passed."
