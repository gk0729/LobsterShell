#!/usr/bin/env python3
"""
一鍵組合測試（蝦殼 + 蝦魂）

用途：
1) 跑 LobsterShell 自身測試
2) 跑可用的 soul_architecture 測試
3) 跑 Shell+Soul 組合 smoke test

適合給 Coder 型 AI 做 API/流程回歸檢查。
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str


def run_cmd(command: List[str], cwd: Path) -> StepResult:
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    passed = result.returncode == 0
    detail = (result.stdout + "\n" + result.stderr).strip()
    return StepResult(
        name=" ".join(command),
        passed=passed,
        detail=detail,
    )


def find_soul_roots(open_code_root: Path) -> List[Path]:
    candidates = [
        open_code_root / "SoulArchitectureSummary" / "soul_architecture",
        open_code_root / "龍蝦換魂記" / "soul_architecture",
    ]
    return [path for path in candidates if path.exists()]


async def run_combo_smoke(shell_root: Path, soul_root: Path, strict_sql: bool) -> StepResult:
    try:
        shell_init = shell_root / "__init__.py"
        shell_spec = importlib.util.spec_from_file_location(
            "LobsterShell_runtime",
            shell_init,
            submodule_search_locations=[str(shell_root)],
        )
        if not shell_spec or not shell_spec.loader:
            return StepResult("combo_smoke", False, "Cannot load LobsterShell runtime module")

        shell_module = importlib.util.module_from_spec(shell_spec)
        shell_spec.loader.exec_module(shell_module)

        sys.path.insert(0, str(soul_root.parent))

        LobsterShellCore = shell_module.LobsterShell
        ToolContext = shell_module.ToolContext
        Permission = shell_module.Permission
        ModeConfig = shell_module.ModeConfig
        from soul_architecture import SoulCore, ExecutionContext, ExecutionMode

        shell = LobsterShellCore(
            mode=ModeConfig.HYBRID_SHIELD,
            enable_sandbox=True,
            audit_enabled=True,
            audit_logger_config={
                "storage_path": str(shell_root / "combo_audit_logs"),
                "max_file_size_bytes": 1024 * 1024,
                "max_backup_files": 2,
                "rotate_by_date": True,
            },
        )

        loaded_tools = await shell.tools.load_directory(str(shell_root / "tools" / "lobster-tool-sql"))

        core = SoulCore(enable_audit=True)

        async def hybrid_executor(context, decision):
            return f"模板輸出: {{'request': '{context.input_content}'}}"

        core.register_executor(ExecutionMode.HYBRID, hybrid_executor)

        soul_result = await core.execute(
            ExecutionContext(
                request_id="combo-req-001",
                session_id="combo-sess-001",
                user_id="combo-user",
                input_content="分析這個數據文件",
                granted_permissions=["ai:use"],
            )
        )

        shell_result = await shell.execute(
            tool_id="sql.readonly_query",
            context=ToolContext(
                user_id="combo-user",
                tenant_id="combo-tenant",
                mode="hybrid_shield",
                session_id="combo-sess-001",
                permissions=[Permission.DATABASE_READ],
                request_id="combo-req-002",
            ),
            params={"query": "SELECT 1", "max_rows": 1},
        )

        messages = []

        if not soul_result.success:
            messages.append(f"Soul failed: {soul_result.error}")

        if "sql.readonly_query" not in loaded_tools:
            messages.append("Shell failed to load sql.readonly_query")

        sql_expected_ok = bool(os.environ.get("DATABASE_URL")) or strict_sql
        if sql_expected_ok and not shell_result.success:
            messages.append(f"SQL execute failed: {shell_result.error}")

        if not shell.verify_audit_chain():
            messages.append("Shell audit chain verification failed")

        if messages:
            return StepResult(
                name="combo_smoke",
                passed=False,
                detail="; ".join(messages),
            )

        info = [
            f"soul_ok={soul_result.success}",
            f"soul_mode={soul_result.mode.value}",
            f"tool_loaded={loaded_tools}",
            f"sql_exec_ok={shell_result.success}",
            f"sql_exec_error={shell_result.error}",
        ]
        return StepResult(name="combo_smoke", passed=True, detail=" | ".join(info))

    except Exception as exc:
        return StepResult(name="combo_smoke", passed=False, detail=str(exc))


def print_result(step: StepResult) -> None:
    status = "PASS" if step.passed else "FAIL"
    print(f"[{status}] {step.name}")
    if step.detail:
        print(step.detail)
        print("-" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="一鍵組合測試（蝦殼 + 蝦魂）")
    parser.add_argument(
        "--strict-sql",
        action="store_true",
        help="要求 SQL 工具執行成功（若未設 DATABASE_URL，預設不視為失敗）",
    )
    args = parser.parse_args()

    shell_root = Path(__file__).resolve().parents[1]
    open_code_root = shell_root.parent

    results: List[StepResult] = []

    # 1) Shell tests
    results.append(run_cmd([sys.executable, "-m", "pytest", "-q"], shell_root))

    # 2) Soul tests (all discovered roots)
    soul_roots = find_soul_roots(open_code_root)
    if not soul_roots:
        results.append(StepResult("soul_tests", False, "No soul_architecture directory found"))
    else:
        for soul in soul_roots:
            suite = run_cmd(
                [sys.executable, "-m", "pytest", "-q", "soul_architecture/test_core.py"],
                soul.parent,
            )
            suite.name = f"soul_tests@{soul.parent.name}"
            results.append(suite)

        # 3) combo smoke (run against first discovered soul root)
        results.append(asyncio.run(run_combo_smoke(shell_root, soul_roots[0], strict_sql=args.strict_sql)))

    for step in results:
        print_result(step)

    all_passed = all(step.passed for step in results)
    print("COMBO_STATUS=PASS" if all_passed else "COMBO_STATUS=FAIL")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
