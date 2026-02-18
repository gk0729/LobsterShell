"""
OpenClaw 適配器 - 包裝 OpenClaw Agent

讓 LobsterShell 可以安全地包裝和控制 OpenClaw
"""

from typing import Any, Optional, Callable
from dataclasses import dataclass
import logging
from importlib import import_module

logger = logging.getLogger(__name__)


@dataclass
class WrappedResponse:
    """包裝後的響應"""
    original_response: Any
    final_output: str
    mode_used: str
    audit_id: str
    local_review: dict
    required_confirmation: bool = False
    user_confirmed: bool = False


class OpenClawAdapter:
    """
    OpenClaw 適配器

    將 OpenClaw Agent 包裝在 LobsterShell 安全層中
    """

    def __init__(
        self,
        openclaw_agent: Any,
        shell,  # LobsterShell 實例
    ):
        self.agent = openclaw_agent
        self.shell = shell

    async def run(
        self,
        request: str,
        context: Optional[dict] = None,
        auto_confirm: bool = False,
    ) -> WrappedResponse:
        """
        安全運行 OpenClaw Agent

        Args:
            request: 用戶請求
            context: 上下文
            auto_confirm: 是否自動確認（危險！）

        Returns:
            WrappedResponse: 包裝後的響應
        """
        calculate_sensitivity = import_module("00_core.mode_controller").calculate_sensitivity

        # 1. 計算敏感度
        sensitivity = calculate_sensitivity(request)

        # 2. 決定模式
        mode_decision = self.shell.mode_controller.decide_mode(
            request=request,
            sensitivity_score=sensitivity,
            context=context,
        )

        logger.info(f"[ModeController] 選擇模式: {mode_decision.mode.value}")

        # 3. 策略檢查
        policy_decision = self.shell.policy_engine.check(
            action="query",  # TODO: 根據請求類型判斷
            content=request,
            context=context,
        )

        if not policy_decision.allowed:
            return WrappedResponse(
                original_response=None,
                final_output=f"⛔ 操作被拒絕: {policy_decision.reason}",
                mode_used=mode_decision.mode.value,
                audit_id="",
                local_review={"allowed": False, "reason": policy_decision.reason},
            )

        # 4. 如果需要確認且不是自動確認
        if policy_decision.requires_confirmation and not auto_confirm:
            # 返回需要確認的響應
            return WrappedResponse(
                original_response=None,
                final_output=f"⚠️ 此操作需要確認: {policy_decision.reason}",
                mode_used=mode_decision.mode.value,
                audit_id="",
                local_review={"requires_confirmation": True},
                required_confirmation=True,
            )

        # 5. 根據模式執行
        if mode_decision.mode.value == "local_only":
            response = await self._run_local(request, context)
        elif mode_decision.mode.value == "hybrid_shield":
            response = await self._run_hybrid(request, context)
        else:
            response = await self._run_cloud_sandbox(request, context)

        # 6. 審計記錄
        audit_entry = self.shell.audit_logger.log(
            action="openclaw_run",
            request=request,
            final_output=response.final_output,
            mode=mode_decision.mode.value,
            policy_decision={
                "allowed": policy_decision.allowed,
                "rule": policy_decision.matched_rule,
            },
        )

        response.audit_id = audit_entry.entry_hash[:16]
        return response

    async def _run_local(
        self,
        request: str,
        context: Optional[dict],
    ) -> WrappedResponse:
        """本地模式運行"""
        logger.info("[Local Mode] 完全本地運行")

        # TODO: 使用本地模型處理
        # 這裡應該調用本地 LLM (Ollama 等)

        return WrappedResponse(
            original_response=None,
            final_output="[本地模式] 處理中... (待實現)",
            mode_used="local_only",
            audit_id="",
            local_review={"mode": "local"},
        )

    async def _run_hybrid(
        self,
        request: str,
        context: Optional[dict],
    ) -> WrappedResponse:
        """混合模式運行"""
        logger.info("[Hybrid Mode] 脫敏 → 雲端 → 本地覆寫")

        # 1. 脫敏處理
        masked_request = self._mask_sensitive_data(request)
        logger.info(f"[Masked] {masked_request}")

        # 2. 發送給雲端 (OpenClaw Agent)
        # cloud_response = await self.agent.run(masked_request)

        # 3. 本地覆寫真實數據
        # final_output = self._overwrite_with_real_data(cloud_response)

        # TODO: 實現完整流程

        return WrappedResponse(
            original_response=None,
            final_output=f"[混合模式] 脫敏後: {masked_request}",
            mode_used="hybrid_shield",
            audit_id="",
            local_review={"mode": "hybrid", "masked": True},
        )

    async def _run_cloud_sandbox(
        self,
        request: str,
        context: Optional[dict],
    ) -> WrappedResponse:
        """雲端沙盒模式"""
        logger.info("[Cloud Sandbox] 沙盒運行 + 本地審核")

        # TODO: 在沙盒中運行，所有 I/O 經本地審核

        return WrappedResponse(
            original_response=None,
            final_output="[雲端沙盒] 處理中... (待實現)",
            mode_used="cloud_sandbox",
            audit_id="",
            local_review={"mode": "cloud_sandbox"},
        )

    def _mask_sensitive_data(self, text: str) -> str:
        """脫敏敏感數據"""
        # TODO: 實現智能脫敏
        # - 手機號 → {{PHONE_001}}
        # - 身份證 → {{IDCARD_001}}
        # - 銀行卡 → {{CARD_001}}
        # - 姓名 → {{USER_001}}

        import re

        # 手機號
        text = re.sub(
            r'1[3-9]\d{9}',
            '{{PHONE}}',
            text
        )

        # 身份證
        text = re.sub(
            r'\d{17}[\dXx]',
            '{{IDCARD}}',
            text
        )

        return text
