#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp_dir="$root_dir/tmp"
backend_pid_file="$tmp_dir/backend.pid"
frontend_pid_file="$tmp_dir/frontend.pid"
backend_log_file="$tmp_dir/backend.log"
frontend_log_file="$tmp_dir/frontend.log"

usage() {
  printf 'Usage: %s [--stop]\n' "$0" >&2
}

is_running() {
  [[ -f "$1" ]] && kill -0 "$(<"$1")" 2>/dev/null
}

wait_for_process() {
  local pid_file="$1"

  for _ in {1..10}; do
    if ! is_running "$pid_file"; then
      return 1
    fi
    sleep 0.1
  done
}

stop_service() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    printf '%s is not running.\n' "$name"
    return
  fi

  local pid
  pid="$(<"$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill -- -"$pid"
    printf 'Stopped %s (PID %s).\n' "$name" "$pid"
  else
    printf '%s PID file was stale.\n' "$name"
  fi
  rm -f "$pid_file"
}

if [[ $# -eq 1 && "$1" == "--stop" ]]; then
  stop_service backend "$backend_pid_file"
  stop_service frontend "$frontend_pid_file"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  usage
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install uv before starting the backend.\n' >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  printf 'npm is required. Install Node.js and npm before starting the frontend.\n' >&2
  exit 1
fi

mkdir -p "$tmp_dir"
if is_running "$backend_pid_file" || is_running "$frontend_pid_file"; then
  printf 'HerpLog is already running. Run %s --stop first.\n' "$0" >&2
  exit 1
fi
rm -f "$backend_pid_file" "$frontend_pid_file"

if [[ ! -d "$root_dir/.venv" ]]; then
  (cd "$root_dir" && uv sync)
fi
if [[ ! -d "$root_dir/frontend/node_modules" ]]; then
  (cd "$root_dir/frontend" && npm install)
fi

if [[ -f "$root_dir/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$root_dir/.env"
  set +a
fi

setsid bash -c '
  cd "$1/backend"
  exec uv run --project "$1" uvicorn main:app --host 127.0.0.1 --port 8000 --reload
' _ "$root_dir" >"$backend_log_file" 2>&1 &
printf '%s\n' "$!" >"$backend_pid_file"

setsid bash -c '
  cd "$1/frontend"
  exec npm run dev -- --strictPort
' _ "$root_dir" >"$frontend_log_file" 2>&1 &
printf '%s\n' "$!" >"$frontend_pid_file"

if ! wait_for_process "$backend_pid_file"; then
  printf 'Backend failed to start. Check %s.\n' "$backend_log_file" >&2
  stop_service backend "$backend_pid_file"
  stop_service frontend "$frontend_pid_file"
  exit 1
fi
if ! wait_for_process "$frontend_pid_file"; then
  printf 'Frontend failed to start. Check %s.\n' "$frontend_log_file" >&2
  stop_service backend "$backend_pid_file"
  stop_service frontend "$frontend_pid_file"
  exit 1
fi

printf 'Backend started (PID %s): %s\n' "$(<"$backend_pid_file")" "$backend_log_file"
printf 'Frontend started (PID %s): %s\n' "$(<"$frontend_pid_file")" "$frontend_log_file"
