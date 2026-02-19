#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

HOST="${HOST:-127.0.0.1}"
OPENCLAW_UPSTREAM_PORT="${OPENCLAW_UPSTREAM_PORT:-18791}"
COMPAT_LISTEN_PORT="${COMPAT_LISTEN_PORT:-18789}"
OPENCLAW_BIN="${OPENCLAW_BIN:-/Users/shinglee/.opencode/bin/opencode}"

OPENCLAW_CMD="${OPENCLAW_CMD:-}"

OPENCLAW_PID=""

cleanup() {
  if [[ -n "${OPENCLAW_PID}" ]]; then
    kill "${OPENCLAW_PID}" >/dev/null 2>&1 || true
  fi
}

wait_port() {
  local host="$1"
  local port="$2"
  local timeout_sec="${3:-30}"
  local elapsed=0

  while [[ "${elapsed}" -lt "${timeout_sec}" ]]; do
    if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  return 1
}

trap cleanup EXIT INT TERM

echo "🦞 One-click 啟動：OpenClaw + LobsterShell 相容層"
echo "   OpenClaw 上游: http://${HOST}:${OPENCLAW_UPSTREAM_PORT}"
echo "   相容入口    : http://${HOST}:${COMPAT_LISTEN_PORT}"

if lsof -nP -iTCP:"${COMPAT_LISTEN_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "❌ ${COMPAT_LISTEN_PORT} 已被占用，請先釋放埠或改 COMPAT_LISTEN_PORT"
  exit 1
fi

if lsof -nP -iTCP:"${OPENCLAW_UPSTREAM_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "ℹ️  偵測到 ${OPENCLAW_UPSTREAM_PORT} 已有服務，略過上游啟動"
else
  if [[ -n "${OPENCLAW_CMD}" ]]; then
    echo "🚀 以自訂 OPENCLAW_CMD 啟動上游"
    bash -lc "${OPENCLAW_CMD}" &
  else
    if [[ ! -x "${OPENCLAW_BIN}" ]]; then
      echo "❌ 找不到可執行檔: ${OPENCLAW_BIN}"
      echo "   請設定 OPENCLAW_CMD 或 OPENCLAW_BIN"
      exit 1
    fi

    echo "🚀 啟動 OpenClaw 上游（opencode serve）"
    "${OPENCLAW_BIN}" serve \
      --hostname "${HOST}" \
      --port "${OPENCLAW_UPSTREAM_PORT}" &
  fi

  OPENCLAW_PID="$!"

  if ! wait_port "${HOST}" "${OPENCLAW_UPSTREAM_PORT}" 40; then
    echo "❌ OpenClaw 上游啟動逾時，請檢查配置"
    exit 1
  fi
fi

echo "✅ 上游就緒，啟動 LobsterShell 相容層..."
cd "${ROOT_DIR}"
exec python3 cli/lobster_cli.py gateway compat \
  --listen-host "${HOST}" \
  --listen-port "${COMPAT_LISTEN_PORT}" \
  --target-url "http://${HOST}:${OPENCLAW_UPSTREAM_PORT}"
