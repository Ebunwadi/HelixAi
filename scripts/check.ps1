$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> API: sync, lint, format, typecheck, test"
Set-Location "$root\apps\api"
python -m uv sync --group dev
python -m uv run ruff check .
python -m uv run ruff format --check .
python -m uv run pyright
python -m uv run pytest

Write-Host "==> Web: install, lint, typecheck, test"
Set-Location "$root\apps\web"
npm ci
npm run lint
npm run typecheck
npm test

Write-Host "==> Docker Compose file is valid"
Set-Location $root
docker compose config | Out-Null

Write-Host "All documented checks passed."
