#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

STOP_SCRIPT="${ROOT_DIR}/scripts/stop_openclaw_compat.sh"
START_SCRIPT="${ROOT_DIR}/scripts/one_click_openclaw_compat.sh"
RESTART_DELAY="${RESTART_DELAY:-1}"

echo "🔄 One-click 重啟：OpenClaw + LobsterShell 相容層"

if [[ ! -x "${STOP_SCRIPT}" ]]; then
  echo "❌ 找不到停止腳本或無執行權限: ${STOP_SCRIPT}"
  exit 1
fi

if [[ ! -x "${START_SCRIPT}" ]]; then
  echo "❌ 找不到啟動腳本或無執行權限: ${START_SCRIPT}"
  exit 1
fi

"${STOP_SCRIPT}" || true
sleep "${RESTART_DELAY}"

exec "${START_SCRIPT}"
