"""
測試: 核心模組

測試 ModeController, PolicyEngine, AuditLogger
"""

import pytest
from datetime import datetime

# 由於我們使用相對導入，需要先安裝或調整路徑
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from 00_core.mode_controller import ModeController, ModeConfig, calculate_sensitivity
from 00_core.policy_engine import PolicyEngine, ActionType, PolicyRule
from 00_core.audit_logger import AuditLogger, AuditLevel


class TestModeController:
    """測試模式控制器"""

    def test_default_mode(self):
        """測試默認模式"""
        controller = ModeController()
        assert controller.default_mode == ModeConfig.HYBRID_SHIELD

    def test_decide_mode_high_sensitivity(self):
        """測試高敏感度請求強制本地模式"""
        controller = ModeController()
        decision = controller.decide_mode(
            request="查詢信用卡餘額",
            sensitivity_score=0.9,
        )
        assert decision.mode == ModeConfig.LOCAL_ONLY
        assert decision.requires_confirmation is True

    def test_decide_mode_low_sensitivity(self):
        """測試低敏感度請求使用雲端模式"""
        controller = ModeController()
        decision = controller.decide_mode(
            request="今天天氣",
            sensitivity_score=0.1,
        )
        assert decision.mode == ModeConfig.CLOUD_SANDBOX

    def test_sensitivity_calculation(self):
        """測試敏感度計算"""
        # 高敏感
        score1 = calculate_sensitivity("轉帳 1000 元")
        assert score1 >= 0.8

        # 中敏感
        score2 = calculate_sensitivity("查詢姓名")
        assert 0.3 <= score2 <= 0.7

        # 低敏感
        score3 = calculate_sensitivity("今天天氣")
        assert score3 < 0.2


class TestPolicyEngine:
    """測試策略引擎"""

    def test_default_rules(self):
        """測試默認規則"""
        engine = PolicyEngine()
        rules = engine.get_rules()
        assert len(rules) > 0
        assert any(r.name == "block_dangerous_sql" for r in rules)

    def test_block_dangerous_sql(self):
        """測試阻止危險 SQL"""
        engine = PolicyEngine()

        # DELETE 應該被拒絕
        decision = engine.check(
            action=ActionType.QUERY,
            content="DELETE FROM users",
        )
        assert decision.allowed is False
        assert decision.risk_level == "critical"

        # DROP 應該被拒絕
        decision = engine.check(
            action=ActionType.QUERY,
            content="DROP TABLE accounts",
        )
        assert decision.allowed is False

    def test_allow_safe_query(self):
        """測試允許安全查詢"""
        engine = PolicyEngine()

        decision = engine.check(
            action=ActionType.QUERY,
            content="SELECT * FROM users WHERE id=1",
        )
        assert decision.allowed is True

    def test_add_custom_rule(self):
        """測試添加自定義規則"""
        engine = PolicyEngine()

        engine.add_rule(PolicyRule(
            name="test_rule",
            description="測試規則",
            allowed_actions=[ActionType.QUERY],
            denied_patterns=[r"test_pattern"],
        ))

        assert engine.get_rule("test_rule") is not None


class TestAuditLogger:
    """測試審計日誌"""

    def test_log_entry(self):
        """測試記錄審計日誌"""
        logger = AuditLogger()

        entry = logger.log(
            action="test_action",
            level=AuditLevel.INFO,
            request="test request",
        )

        assert entry.action == "test_action"
        assert entry.entry_hash is not None

    def test_chain_integrity(self):
        """測試鏈完整性"""
        logger = AuditLogger()

        # 記錄多條日誌
        for i in range(5):
            logger.log(action=f"action_{i}")

        # 驗證鏈
        assert logger.verify_chain() is True

    def test_search(self):
        """測試搜索日誌"""
        logger = AuditLogger()

        logger.log(action="search_test", user_id="user_001")
        logger.log(action="other_action", user_id="user_002")

        results = logger.search(user_id="user_001")
        assert len(results) == 1
        assert results[0].action == "search_test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
