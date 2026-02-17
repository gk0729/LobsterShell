"""
三模式控制器 - LobsterShell 核心

模式:
- LOCAL_ONLY: 完全本地運行，0 資料外洩
- HYBRID_SHIELD: 雲端 AI 只看 Token，本地覆寫真實數據
- CLOUD_SANDBOX: 強製沙盒，所有 I/O 經本地審核
"""

from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ModeConfig(Enum):
    """三種安全模式"""
    LOCAL_ONLY = "local_only"          # 完全本地
    HYBRID_SHIELD = "hybrid_shield"    # 混合模式
    CLOUD_SANDBOX = "cloud_sandbox"    # 雲端沙盒


@dataclass
class ModeDecision:
    """模式決策結果"""
    mode: ModeConfig
    reason: str
    confidence: float
    requires_confirmation: bool = False
    blocked: bool = False


class ModeController:
    """
    三模式控制器

    根據請求類型、敏感度、用戶設定決定使用哪種模式
    """

    def __init__(
        self,
        default_mode: ModeConfig = ModeConfig.HYBRID_SHIELD,
        local_threshold: float = 0.8,  # 敏感度高於此值強制本地
        cloud_threshold: float = 0.3,  # 敏感度低於此值可用雲端
    ):
        self.default_mode = default_mode
        self.local_threshold = local_threshold
        self.cloud_threshold = cloud_threshold
        self._mode_overrides: dict[str, ModeConfig] = {}

    def decide_mode(
        self,
        request: str,
        sensitivity_score: float,
        user_preferences: Optional[dict] = None,
        context: Optional[dict] = None,
    ) -> ModeDecision:
        """
        決定使用哪種模式處理請求

        Args:
            request: 用戶請求文本
            sensitivity_score: 敏感度評分 (0-1)
            user_preferences: 用戶偏好設定
            context: 額外上下文

        Returns:
            ModeDecision: 模式決策結果
        """
        # 1. 檢查是否有強制模式覆蓋
        request_hash = hash(request)
        if request_hash in self._mode_overrides:
            mode = self._mode_overrides[request_hash]
            return ModeDecision(
                mode=mode,
                reason="用戶指定模式覆蓋",
                confidence=1.0,
            )

        # 2. 根據敏感度決定模式
        if sensitivity_score >= self.local_threshold:
            return ModeDecision(
                mode=ModeConfig.LOCAL_ONLY,
                reason=f"敏感度 {sensitivity_score:.2f} 超過閾值 {self.local_threshold}",
                confidence=0.95,
                requires_confirmation=True,
            )

        if sensitivity_score <= self.cloud_threshold:
            return ModeDecision(
                mode=ModeConfig.CLOUD_SANDBOX,
                reason=f"敏感度 {sensitivity_score:.2f} 低於閾值 {self.cloud_threshold}",
                confidence=0.85,
            )

        # 3. 默認混合模式
        return ModeDecision(
            mode=ModeConfig.HYBRID_SHIELD,
            reason="使用默認混合模式",
            confidence=0.8,
            requires_confirmation=(sensitivity_score > 0.5),
        )

    def set_override(self, request_pattern: str, mode: ModeConfig):
        """為特定請求模式設置模式覆蓋"""
        self._mode_overrides[request_pattern] = mode

    def clear_overrides(self):
        """清除所有模式覆蓋"""
        self._mode_overrides.clear()


# 敏感度評分關鍵詞
SENSITIVE_KEYWORDS = {
    # 金融
    "轉帳": 0.9,
    "餘額": 0.8,
    "密碼": 0.95,
    "信用卡": 0.85,
    "銀行": 0.7,
    
    # 個人資料
    "身份證": 0.95,
    "手機號": 0.7,
    "地址": 0.6,
    "姓名": 0.5,
    
    # 系統操作
    "刪除": 0.8,
    "修改": 0.7,
    "執行": 0.6,
    "drop": 0.95,
    "delete": 0.9,
}


def calculate_sensitivity(request: str) -> float:
    """
    計算請求的敏感度評分

    Args:
        request: 用戶請求文本

    Returns:
        float: 敏感度評分 (0-1)
    """
    request_lower = request.lower()
    scores = []

    for keyword, score in SENSITIVE_KEYWORDS.items():
        if keyword in request_lower:
            scores.append(score)

    if not scores:
        return 0.1  # 默認低敏感度

    # 取最高分
    return max(scores)
