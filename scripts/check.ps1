$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> API: sync, lint, format, typecheck, test"
Set-Location "$root\apps\api"
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest

Write-Host "==> Web: install, lint, typecheck, test, build"
Set-Location "$root\apps\web"
npm ci
npm run lint
npm run typecheck
npm test
npm run build

Write-Host "==> Docker Compose file is valid"
Set-Location $root
docker compose config | Out-Null

Write-Host "All documented checks passed."
