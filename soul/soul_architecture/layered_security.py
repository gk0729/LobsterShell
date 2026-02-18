"""
分層安全檢查系統 - Layered Security System
=============================================
核心能力：多階段、Fail-Fast 的安全檢查架構

設計原則:
- Phase 1: 入口檢查 (身份/授權/租戶隔離)
- Phase 2: 內容檢查 (注入/PII/憑證洩漏)
- Phase 3: 行為檢查 (工具白名單/危險操作)
- Phase 4: 執行檢查 (SQL只讀/參數校驗)

每個 Phase 內部 Fail-Fast，Phase 之間可配置是否繼續
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod
import re
import logging

logger = logging.getLogger(__name__)


class SecurityPhase(Enum):
    """安全檢查階段"""
    ENTRY = 1       # 入口檢查
    CONTENT = 2     # 內容檢查
    BEHAVIOR = 3    # 行為檢查
    EXECUTION = 4   # 執行檢查


class Severity(Enum):
    """嚴重性級別"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """檢查結果"""
    check_id: str
    passed: bool
    message: str
    severity: Severity
    phase: SecurityPhase
    details: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None  # 修復建議


@dataclass
class SecurityReport:
    """安全檢查報告"""
    overall_passed: bool
    results: List[CheckResult]
    phase_summary: Dict[SecurityPhase, Dict[str, Any]]
    risk_level: str  # low/medium/high/critical
    timestamp: str


class SecurityCheck(ABC):
    """安全檢查基類"""
    
    def __init__(
        self,
        check_id: str,
        name: str,
        phase: SecurityPhase,
        severity: Severity = Severity.MEDIUM,
        enabled: bool = True,
    ):
        self.check_id = check_id
        self.name = name
        self.phase = phase
        self.severity = severity
        self.enabled = enabled
    
    @abstractmethod
    def check(self, context: Dict[str, Any]) -> CheckResult:
        """執行檢查，子類必須實現"""
        pass
    
    def fail(self, message: str, details: Optional[Dict] = None, remediation: Optional[str] = None) -> CheckResult:
        """快速生成失敗結果"""
        return CheckResult(
            check_id=self.check_id,
            passed=False,
            message=message,
            severity=self.severity,
            phase=self.phase,
            details=details or {},
            remediation=remediation,
        )
    
    def pass_(self, message: str = "通過", details: Optional[Dict] = None) -> CheckResult:
        """快速生成通過結果"""
        return CheckResult(
            check_id=self.check_id,
            passed=True,
            message=message,
            severity=self.severity,
            phase=self.phase,
            details=details or {},
        )


# ===== 具體檢查實現 =====

class AuthenticationCheck(SecurityCheck):
    """身份驗證檢查"""
    
    def __init__(self):
        super().__init__(
            check_id="SEC-001",
            name="身份驗證",
            phase=SecurityPhase.ENTRY,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        user_id = context.get("user_id")
        token = context.get("auth_token")
        
        if not user_id:
            return self.fail(
                "缺少用戶身份",
                remediation="請提供有效的用戶認證信息"
            )
        
        if not token:
            return self.fail(
                "缺少認證令牌",
                remediation="請提供有效的認證令牌"
            )
        
        # TODO: 驗證 token 有效性
        return self.pass_(f"用戶 {user_id} 已認證")


class AuthorizationCheck(SecurityCheck):
    """授權檢查"""
    
    def __init__(self):
        super().__init__(
            check_id="SEC-002",
            name="權限檢查",
            phase=SecurityPhase.ENTRY,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        required = set(context.get("required_permissions", []))
        granted = set(context.get("granted_permissions", []))
        
        missing = required - granted
        if missing:
            return self.fail(
                f"缺少權限: {missing}",
                {"missing": list(missing), "granted": list(granted)},
                f"請申請以下權限: {', '.join(missing)}"
            )
        
        return self.pass_(f"權限檢查通過 ({len(granted)} 個權限)")


class PromptInjectionCheck(SecurityCheck):
    """Prompt 注入檢測"""
    
    # 已知的注入模式
    INJECTION_PATTERNS = [
        (r'ignore\s+previous\s+instructions', "忽略先前指令"),
        (r'disregard\s+all\s+above', "忽視上述內容"),
        (r'system:\s*you\s+are', "系統角色覆寫"),
        (r'\[system\]', "系統標籤注入"),
        (r'<<\s*(?:system|admin|root)\s*>>', "偽造系統標記"),
        (r'###\s*(?:instruction|system)', "偽造指令分隔"),
        (r'forget\s+(?:everything|all)', "遺忘指令"),
        (r'you\s+are\s+now', "角色切換嘗試"),
    ]
    
    def __init__(self):
        super().__init__(
            check_id="SEC-010",
            name="Prompt 注入檢測",
            phase=SecurityPhase.CONTENT,
            severity=Severity.HIGH,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        content = context.get("content", "").lower()
        
        for pattern, desc in self.INJECTION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"檢測到 Prompt 注入: {desc}")
                return self.fail(
                    f"檢測到注入模式: {desc}",
                    {"pattern": pattern, "detected": desc},
                    "請移除可疑的指令覆寫內容"
                )
        
        return self.pass_("未檢測到注入模式")


class PIIDetectionCheck(SecurityCheck):
    """個人身份信息檢測"""
    
    PII_PATTERNS = {
        "email": (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "電子郵件"),
        "phone": (r'\b(?:\+?86)?1[3-9]\d{9}\b', "手機號碼"),
        "ssn": (r'\b\d{17}[\dXx]\b', "身份證號"),  # 簡化版
        "credit_card": (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', "信用卡號"),
    }
    
    def __init__(self):
        super().__init__(
            check_id="SEC-020",
            name="PII 檢測",
            phase=SecurityPhase.CONTENT,
            severity=Severity.MEDIUM,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        content = context.get("content", "")
        detected = {}
        
        for pii_type, (pattern, name) in self.PII_PATTERNS.items():
            matches = re.findall(pattern, content)
            if matches:
                detected[pii_type] = {"name": name, "count": len(matches)}
        
        if detected:
            # PII 檢測通過但需要標記
            context["pii_detected"] = list(detected.keys())
            return CheckResult(
                check_id=self.check_id,
                passed=True,  # 通過但需處理
                message=f"檢測到 PII: {list(detected.keys())}",
                severity=self.severity,
                phase=self.phase,
                details={"detected": detected},
                remediation="建議使用 Token 化或脫敏處理",
            )
        
        return self.pass_("未檢測到 PII")


class SQLInjectionCheck(SecurityCheck):
    """SQL 注入檢測"""
    
    SQL_INJECTION_PATTERNS = [
        (r"--\s*$", "註釋攻擊"),
        (r";\s*(?:DROP|DELETE|UPDATE|INSERT)", "堆疊查詢"),
        (r"'\s*(?:OR|AND)\s*['\"]?\s*\d*\s*=\s*\d*", "邏輯繞過"),
        (r"UNION\s+(?:ALL\s+)?SELECT", "UNION 注入"),
        (r"EXEC\s*\(", "存儲過程執行"),
        (r"\/\*!?\s*\*\/", "註釋繞過"),
    ]
    
    def __init__(self):
        super().__init__(
            check_id="SEC-030",
            name="SQL 注入檢測",
            phase=SecurityPhase.EXECUTION,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        sql = context.get("sql", "")
        
        for pattern, desc in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"檢測到 SQL 注入: {desc}")
                return self.fail(
                    f"檢測到 SQL 注入風險: {desc}",
                    {"pattern": pattern, "sql_snippet": sql[:100]},
                    "請使用參數化查詢或預處理語句"
                )
        
        return self.pass_("SQL 語句安全")


class SQLReadOnlyCheck(SecurityCheck):
    """SQL 只讀檢查"""
    
    WRITE_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP",
        "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"
    ]
    
    def __init__(self):
        super().__init__(
            check_id="SEC-031",
            name="SQL 只讀檢查",
            phase=SecurityPhase.EXECUTION,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        sql = context.get("sql", "").upper()
        
        for keyword in self.WRITE_KEYWORDS:
            if keyword in sql:
                return self.fail(
                    f"檢測到寫入操作: {keyword}",
                    {"keyword": keyword, "operation": "WRITE"},
                    "當前只允許 SELECT 查詢"
                )
        
        return self.pass_("確認為只讀操作")


class ToolWhitelistCheck(SecurityCheck):
    """工具白名單檢查"""
    
    def __init__(self):
        super().__init__(
            check_id="SEC-040",
            name="工具白名單",
            phase=SecurityPhase.BEHAVIOR,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        tool_name = context.get("tool_name")
        whitelist = context.get("tool_whitelist", [])
        
        if not whitelist:
            return self.fail(
                "未配置工具白名單",
                remediation="請先配置允許使用的工具列表"
            )
        
        if tool_name not in whitelist:
            return self.fail(
                f"工具 '{tool_name}' 不在白名單中",
                {"tool": tool_name, "whitelist": whitelist},
                f"請使用以下允許的工具: {', '.join(whitelist)}"
            )
        
        return self.pass_(f"工具 '{tool_name}' 已授權")


class DangerousToolCheck(SecurityCheck):
    """危險工具檢測"""
    
    DANGEROUS_PATTERNS = [
        (r"\beval\s*\(", "eval 執行"),
        (r"\bexec\s*\(", "exec 執行"),
        (r"\bos\.system\s*\(", "系統命令"),
        (r"\bsubprocess\.", "子進程"),
        (r"\brm\s+-rf\s+\/", "危險刪除"),
        (r"\bdd\s+if=.+of=\/dev", "磁盤操作"),
    ]
    
    def __init__(self):
        super().__init__(
            check_id="SEC-041",
            name="危險工具檢測",
            phase=SecurityPhase.BEHAVIOR,
            severity=Severity.CRITICAL,
        )
    
    def check(self, context: Dict[str, Any]) -> CheckResult:
        tool_code = context.get("tool_code", "")
        
        for pattern, desc in self.DANGEROUS_PATTERNS:
            if re.search(pattern, tool_code, re.IGNORECASE):
                return self.fail(
                    f"檢測到危險操作: {desc}",
                    {"pattern": pattern, "description": desc},
                    "該操作被安全策略禁止"
                )
        
        return self.pass_("未檢測到危險操作")


class LayeredSecuritySystem:
    """
    分層安全檢查系統
    
    協調多階段安全檢查，支持 Fail-Fast 和完整報告模式
    """
    
    def __init__(self, fail_fast: bool = True):
        self.checks: List[SecurityCheck] = []
        self.fail_fast = fail_fast
        self._register_default_checks()
    
    def _register_default_checks(self):
        """註冊默認檢查"""
        # Phase 1: 入口檢查
        self.register(AuthenticationCheck())
        self.register(AuthorizationCheck())
        
        # Phase 2: 內容檢查
        self.register(PromptInjectionCheck())
        self.register(PIIDetectionCheck())
        
        # Phase 3: 行為檢查
        self.register(ToolWhitelistCheck())
        self.register(DangerousToolCheck())
        
        # Phase 4: 執行檢查
        self.register(SQLInjectionCheck())
        self.register(SQLReadOnlyCheck())
    
    def register(self, check: SecurityCheck):
        """註冊檢查"""
        self.checks.append(check)
        logger.info(f"註冊安全檢查: {check.check_id} - {check.name}")
    
    def run_phase(
        self,
        phase: SecurityPhase,
        context: Dict[str, Any],
    ) -> List[CheckResult]:
        """執行特定階段的所有檢查"""
        results = []
        
        for check in self.checks:
            if check.phase != phase or not check.enabled:
                continue
            
            try:
                result = check.check(context)
                results.append(result)
                
                # Fail-Fast: 嚴重失敗時立即停止
                if self.fail_fast and not result.passed:
                    if result.severity in [Severity.CRITICAL, Severity.HIGH]:
                        logger.warning(f"[{phase.name}] 檢查失敗，停止後續檢查: {check.check_id}")
                        break
                        
            except Exception as e:
                logger.exception(f"檢查異常: {check.check_id}")
                results.append(CheckResult(
                    check_id=check.check_id,
                    passed=False,
                    message=f"檢查異常: {str(e)}",
                    severity=Severity.CRITICAL,
                    phase=phase,
                    details={"error": str(e)},
                ))
                if self.fail_fast:
                    break
        
        return results
    
    def run_all(self, context: Dict[str, Any]) -> SecurityReport:
        """執行所有階段檢查"""
        all_results = []
        phase_summary = {}
        
        for phase in SecurityPhase:
            results = self.run_phase(phase, context)
            all_results.extend(results)
            
            passed = sum(1 for r in results if r.passed)
            failed = len(results) - passed
            
            phase_summary[phase] = {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "critical": sum(1 for r in results if not r.passed and r.severity == Severity.CRITICAL),
            }
            
            # 如果某個 Phase 有關鍵失敗，可以選擇停止
            if self.fail_fast and phase_summary[phase]["critical"] > 0:
                logger.warning(f"Phase {phase.name} 有嚴重安全問題，終止後續檢查")
                break
        
        # 計算整體風險等級
        critical_count = sum(1 for r in all_results if not r.passed and r.severity == Severity.CRITICAL)
        high_count = sum(1 for r in all_results if not r.passed and r.severity == Severity.HIGH)
        
        if critical_count > 0:
            risk_level = "critical"
        elif high_count > 0:
            risk_level = "high"
        elif any(not r.passed for r in all_results):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        from datetime import datetime
        return SecurityReport(
            overall_passed=all(r.passed for r in all_results),
            results=all_results,
            phase_summary=phase_summary,
            risk_level=risk_level,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def generate_report_text(self, report: SecurityReport) -> str:
        """生成可讀的安全報告"""
        lines = [
            "=" * 50,
            "🔒 安全檢查報告",
            "=" * 50,
            f"整體狀態: {'✅ 通過' if report.overall_passed else '❌ 未通過'}",
            f"風險等級: {report.risk_level.upper()}",
            f"檢查時間: {report.timestamp}",
            "-" * 50,
        ]
        
        # 按 Phase 分組顯示
        for phase in SecurityPhase:
            if phase not in report.phase_summary:
                continue
                
            summary = report.phase_summary[phase]
            lines.append(f"\n📋 Phase {phase.value}: {phase.name}")
            lines.append(f"   通過: {summary['passed']}/{summary['total']}")
            
            if summary['failed'] > 0:
                phase_results = [r for r in report.results if r.phase == phase]
                for result in phase_results:
                    status = "✅" if result.passed else "❌"
                    lines.append(f"   {status} [{result.check_id}] {result.message}")
                    if not result.passed and result.remediation:
                        lines.append(f"      💡 建議: {result.remediation}")
        
        lines.append("=" * 50)
        return "\n".join(lines)
