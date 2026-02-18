"""
🦞 LobsterShell Soul Architecture
=====================================
抽取 LobsterShell 核心靈魂：主動思考動態解決問題的行為邏輯

核心設計原則:
1. 主動感知 → 動態決策 → 分層執行 → 結果覆寫
2. 敏感度驅動的執行模式切換
3. 多階段安全檢查（Fail-Fast）
4. AI 零幻覺：猜測值 → 精確數據覆寫
"""

from .dynamic_mode_engine import (
    DynamicModeEngine,
    ExecutionMode,
    ModeDecision,
    SensitivityAnalyzer,
)
from .layered_security import (
    LayeredSecuritySystem,
    SecurityPhase,
    SecurityCheck,
    CheckResult,
    Severity,
)
from .zero_hallucination_overwriter import (
    ZeroHallucinationOverwriter,
    DataSource,
    OverwriteRule,
    QueryRunner,
)
from .audit_chain import (
    AuditChain,
    AuditEntry,
    AuditLevel,
)
from .soul_core import SoulCore, ExecutionContext, ExecutionResult

__version__ = "1.0.0"
__all__ = [
    # 靈魂核心
    "SoulCore",
    "ExecutionContext",
    "ExecutionResult",
    # 動態模式引擎
    "DynamicModeEngine",
    "ExecutionMode",
    "ModeDecision",
    "SensitivityAnalyzer",
    # 分層安全系統
    "LayeredSecuritySystem",
    "SecurityPhase",
    "SecurityCheck",
    "CheckResult",
    "Severity",
    # 零幻覺覆寫層
    "ZeroHallucinationOverwriter",
    "DataSource",
    "OverwriteRule",
    "QueryRunner",
    # 審計鏈
    "AuditChain",
    "AuditEntry",
    "AuditLevel",
]
