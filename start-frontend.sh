#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'npm is required. Install Node.js and npm before starting the frontend.\n' >&2
  exit 1
fi

if [[ ! -d "$root_dir/frontend/node_modules" ]]; then
  (cd "$root_dir/frontend" && npm install)
fi

cd "$root_dir/frontend"
exec npm run dev -- --strictPort
