"""
策略引擎 - LobsterShell 安全策略核心

定義誰能幹什麼、何時幹、怎麼幹
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """操作類型"""
    QUERY = "query"           # 查詢
    CREATE = "create"         # 創建
    UPDATE = "update"         # 更新
    DELETE = "delete"         # 刪除
    EXECUTE = "execute"       # 執行
    EXPORT = "export"         # 導出
    IMPORT = "import"         # 導入


@dataclass
class PolicyRule:
    """策略規則"""
    name: str
    description: str
    allowed_actions: list[ActionType]
    denied_patterns: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    max_rate: Optional[int] = None  # 每分鐘最大次數
    time_restrictions: Optional[dict] = None  # 時間限制


@dataclass
class PolicyDecision:
    """策略決策結果"""
    allowed: bool
    reason: str
    matched_rule: Optional[str] = None
    requires_confirmation: bool = False
    risk_level: str = "low"  # low, medium, high, critical


class PolicyEngine:
    """
    策略引擎

    負責檢查所有操作是否符合安全策略
    """

    def __init__(self):
        self._rules: dict[str, PolicyRule] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """設置默認安全規則"""

        # 規則 1: 禁止危險 SQL 操作
        self.add_rule(PolicyRule(
            name="block_dangerous_sql",
            description="禁止 DELETE/DROP/TRUNCATE 等 SQL 操作",
            allowed_actions=[ActionType.QUERY],
            denied_patterns=[
                r"\bDELETE\s+FROM\b",
                r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
                r"\bTRUNCATE\s+TABLE?\b",
                r"\bUPDATE\s+.*\bSET\b",
                r"\bINSERT\s+INTO\b",
            ],
            requires_confirmation=False,  # 直接拒絕
        ))

        # 規則 2: 敏感數據查詢需確認
        self.add_rule(PolicyRule(
            name="sensitive_data_access",
            description="查詢敏感數據需要用戶確認",
            allowed_actions=[ActionType.QUERY],
            denied_patterns=[],
            requires_confirmation=True,
        ))

        # 規則 3: 系統命令限制
        self.add_rule(PolicyRule(
            name="system_command_restriction",
            description="系統命令執行限制",
            allowed_actions=[ActionType.EXECUTE],
            denied_patterns=[
                r"\brm\s+-rf\b",
                r"\bsudo\s+",
                r"\bchmod\s+777\b",
                r">\s*/dev/",
            ],
            requires_confirmation=True,
        ))

    def add_rule(self, rule: PolicyRule):
        """添加策略規則"""
        self._rules[rule.name] = rule
        logger.info(f"Added policy rule: {rule.name}")

    def check(
        self,
        action: ActionType,
        content: str,
        context: Optional[dict] = None,
    ) -> PolicyDecision:
        """
        檢查操作是否符合策略

        Args:
            action: 操作類型
            content: 操作內容
            context: 上下文信息

        Returns:
            PolicyDecision: 策略決策結果
        """
        content_lower = content.lower()

        for rule_name, rule in self._rules.items():
            # 檢查操作類型是否允許
            if action not in rule.allowed_actions:
                continue

            # 檢查是否匹配拒絕模式
            for pattern in rule.denied_patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return PolicyDecision(
                        allowed=False,
                        reason=f"匹配拒絕模式: {pattern}",
                        matched_rule=rule_name,
                        risk_level="critical",
                    )

            # 如果是需要確認的規則
            if rule.requires_confirmation:
                return PolicyDecision(
                    allowed=True,
                    reason="需要用戶確認",
                    matched_rule=rule_name,
                    requires_confirmation=True,
                    risk_level="medium",
                )

        # 默認允許
        return PolicyDecision(
            allowed=True,
            reason="未匹配任何限制規則",
            risk_level="low",
        )

    def get_rules(self) -> list[PolicyRule]:
        """獲取所有規則"""
        return list(self._rules.values())

    def remove_rule(self, rule_name: str) -> bool:
        """移除規則"""
        if rule_name in self._rules:
            del self._rules[rule_name]
            return True
        return False
