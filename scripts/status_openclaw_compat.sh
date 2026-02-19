#!/usr/bin/env bash

set -euo pipefail

COMPAT_LISTEN_PORT="${COMPAT_LISTEN_PORT:-18789}"
OPENCLAW_UPSTREAM_PORT="${OPENCLAW_UPSTREAM_PORT:-18791}"

show_port_status() {
  local port="$1"
  local label="$2"
  local rows

  rows="$(lsof -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "${rows}" ]]; then
    echo "❌ ${label} (${port}): OFFLINE"
    return 0
  fi

  echo "✅ ${label} (${port}): ONLINE"
  echo "${rows}" | awk 'NR==1 || NR>1 {print "   " $0}'
}

echo "🦞 OpenClaw 相容棧狀態"
echo ""
show_port_status "${COMPAT_LISTEN_PORT}" "LobsterShell 相容層"
echo ""
show_port_status "${OPENCLAW_UPSTREAM_PORT}" "OpenClaw 上游"
