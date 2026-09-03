#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install uv before starting the backend.\n' >&2
  exit 1
fi

if [[ ! -d "$root_dir/.venv" ]]; then
  (cd "$root_dir" && uv sync)
fi

if [[ -f "$root_dir/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$root_dir/.env"
  set +a
fi

(cd "$root_dir" && uv run --project "$root_dir" alembic upgrade head)

cd "$root_dir/backend"
exec uv run --project "$root_dir" uvicorn main:app --host 127.0.0.1 --port 8000 --reload
