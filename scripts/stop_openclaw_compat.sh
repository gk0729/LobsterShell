#!/usr/bin/env bash

set -euo pipefail

COMPAT_LISTEN_PORT="${COMPAT_LISTEN_PORT:-18789}"
OPENCLAW_UPSTREAM_PORT="${OPENCLAW_UPSTREAM_PORT:-18791}"

stop_port() {
  local port="$1"
  local label="$2"
  local pids

  pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "${pids}" ]]; then
    echo "ℹ️  ${label} (${port}) 沒有在執行"
    return 0
  fi

  echo "🛑 停止 ${label} (${port}): ${pids}"
  kill ${pids} >/dev/null 2>&1 || true

  sleep 1
  pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "⚠️  強制停止 ${label} (${port}): ${pids}"
    kill -9 ${pids} >/dev/null 2>&1 || true
  fi
}

echo "🦞 One-click 停止：OpenClaw + LobsterShell 相容層"

stop_port "${COMPAT_LISTEN_PORT}" "LobsterShell 相容層"
stop_port "${OPENCLAW_UPSTREAM_PORT}" "OpenClaw 上游"

echo "✅ 完成"
