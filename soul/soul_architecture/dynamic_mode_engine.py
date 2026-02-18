"""
動態模式決策引擎 - Dynamic Mode Engine
========================================
核心能力：主動感知輸入敏感度，動態選擇最適執行模式

設計原則:
- 敏感度評估 → 模式匹配 → 動態路由
- 支持用戶覆寫 + 智能推薦
- 置信度驅動的決策透明度
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """三種執行模式"""
    LOCAL_ONLY = "local_only"          # 完全本地，零外洩
    HYBRID = "hybrid"                   # 混合模式：雲端思考 + 本地執行
    CLOUD_SANDBOX = "cloud_sandbox"     # 雲端沙盒：輕量脫敏後上雲


@dataclass
class ModeDecision:
    """模式決策結果"""
    mode: ExecutionMode
    confidence: float                    # 置信度 0-1
    reason: str                          # 決策原因
    sensitivity_score: float             # 敏感度評分
    requires_confirmation: bool = False  # 是否需要用戶確認
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class SensitivityRule:
    """敏感度規則"""
    pattern: str                         # 正則或關鍵詞
    score: float                         # 敏感度分數 0-1
    category: str                        # 類別：金融/個資/系統等
    is_regex: bool = False


class SensitivityAnalyzer:
    """
    敏感度分析器
    
    主動分析輸入內容的敏感程度，為模式決策提供依據
    """
    
    # 預設敏感度規則庫（支持簡/繁中文）
    DEFAULT_RULES = [
        # 金融類 (高敏感)
        SensitivityRule(r"密碼|密码|password|密鑰|密钥|private.?key", 0.95, "credential", is_regex=True),
        SensitivityRule(r"信用卡|credit.?card|CVV|\b\d{16}\b", 0.9, "financial", is_regex=True),
        SensitivityRule(r"轉帳|转账|匯款|汇款|transfer|balance", 0.85, "financial", is_regex=True),
        SensitivityRule(r"銀行帳號|银行账号|account.?number", 0.8, "financial", is_regex=True),

        # 個人身份類 (中高敏感)
        SensitivityRule(r"身份證|身份证|ID.?card|身分證|身分证", 0.95, "identity", is_regex=True),
        SensitivityRule(r"護照|护照|passport", 0.9, "identity", is_regex=True),
        SensitivityRule(r"手機號|手机号|phone|\b\d{11}\b", 0.7, "identity", is_regex=True),
        SensitivityRule(r"地址|address|住址", 0.6, "identity", is_regex=True),
        SensitivityRule(r"姓名|name", 0.5, "identity", is_regex=True),

        # 系統操作類 (中高敏感)
        SensitivityRule(r"刪除|删除|delete|drop|truncate", 0.85, "system", is_regex=True),
        SensitivityRule(r"修改|update|alter", 0.75, "system", is_regex=True),
        SensitivityRule(r"執行|执行|exec|eval|system", 0.7, "system", is_regex=True),
        SensitivityRule(r"rm\s+-rf|chmod\s+777", 0.95, "system", is_regex=True),

        # 商業機密類
        SensitivityRule(r"營業額|营业额|revenue|profit", 0.75, "business", is_regex=True),
        SensitivityRule(r"客戶名單|客户名单|customer.?list", 0.8, "business", is_regex=True),
        SensitivityRule(r"合約|合约|contract|agreement", 0.6, "business", is_regex=True),
    ]
    
    def __init__(self, custom_rules: Optional[List[SensitivityRule]] = None):
        self.rules = custom_rules or self.DEFAULT_RULES.copy()
        self._pattern_cache: Dict[str, re.Pattern] = {}
    
    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析內容敏感度
        
        Args:
            content: 要分析的內容
            context: 額外上下文
            
        Returns:
            {
                "score": float,           # 最高敏感度分數
                "matched_rules": list,    # 匹配的規則
                "categories": list,       # 涉及的類別
                "details": dict           # 詳細分析
            }
        """
        # 注意：對於正則表達式規則，使用原始內容（不轉小寫）
        # 因為中文等非 ASCII 字符不受 lower() 影響
        matched_rules = []
        categories = set()
        
        for rule in self.rules:
            if self._matches(content, rule):
                matched_rules.append(rule)
                categories.add(rule.category)
        
        # 計算綜合敏感度分數
        if matched_rules:
            # 取最高分 + 數量加權
            base_score = max(r.score for r in matched_rules)
            count_bonus = min(len(matched_rules) * 0.05, 0.15)  # 最多加 0.15
            final_score = min(base_score + count_bonus, 1.0)
        else:
            final_score = 0.1  # 默認低敏感度
        
        # 上下文調整
        if context:
            final_score = self._adjust_by_context(final_score, context)
        
        return {
            "score": round(final_score, 2),
            "matched_rules": matched_rules,
            "categories": list(categories),
            "details": {
                "rule_count": len(matched_rules),
                "content_length": len(content),
                "has_pii": "identity" in categories,
                "has_credential": "credential" in categories,
            }
        }
    
    def _matches(self, content: str, rule: SensitivityRule) -> bool:
        """檢查內容是否匹配規則"""
        if rule.is_regex:
            pattern = self._pattern_cache.get(rule.pattern)
            if not pattern:
                pattern = re.compile(rule.pattern, re.IGNORECASE)
                self._pattern_cache[rule.pattern] = pattern
            return bool(pattern.search(content))
        else:
            return rule.pattern.lower() in content
    
    def _adjust_by_context(self, score: float, context: Dict[str, Any]) -> float:
        """根據上下文調整分數"""
        # 用戶明確標記高敏感
        if context.get("user_marked_sensitive"):
            score = max(score, 0.9)
        
        # 來自高權限用戶
        if context.get("is_admin"):
            score = min(score * 1.1, 1.0)
        
        # 生產環境提高敏感度
        if context.get("environment") == "production":
            score = min(score * 1.15, 1.0)
        
        return score
    
    def add_rule(self, rule: SensitivityRule):
        """添加自定義規則"""
        self.rules.append(rule)


class DynamicModeEngine:
    """
    動態模式決策引擎
    
    核心能力：根據輸入敏感度動態選擇執行模式
    
    決策邏輯:
    - score >= 0.8  → LOCAL_ONLY (強制本地)
    - score <= 0.3  → CLOUD_SANDBOX (可上雲)
    - 0.3 < score < 0.8 → HYBRID (混合模式)
    """
    
    def __init__(
        self,
        local_threshold: float = 0.8,
        cloud_threshold: float = 0.3,
        default_mode: ExecutionMode = ExecutionMode.HYBRID,
    ):
        self.analyzer = SensitivityAnalyzer()
        self.local_threshold = local_threshold
        self.cloud_threshold = cloud_threshold
        self.default_mode = default_mode
        
        # 用戶覆寫規則
        self._user_overrides: Dict[str, ExecutionMode] = {}
        
        # 自定義決策回調
        self._decision_hooks: List[Callable[[Dict], Optional[ModeDecision]]] = []
    
    def decide(
        self,
        content: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ModeDecision:
        """
        決定執行模式
        
        Args:
            content: 輸入內容
            user_id: 用戶ID
            context: 額外上下文
            
        Returns:
            ModeDecision: 模式決策結果
        """
        # 1. 檢查用戶覆寫
        override = self._check_override(content, user_id)
        if override:
            return override
        
        # 2. 執行敏感度分析
        analysis = self.analyzer.analyze(content, context)
        score = analysis["score"]
        
        # 3. 執行自定義決策鉤子
        for hook in self._decision_hooks:
            custom_decision = hook({
                "content": content,
                "score": score,
                "analysis": analysis,
                "context": context,
            })
            if custom_decision:
                return custom_decision
        
        # 4. 標準決策邏輯
        return self._make_decision(score, analysis, context)
    
    def _check_override(
        self,
        content: str,
        user_id: Optional[str],
    ) -> Optional[ModeDecision]:
        """檢查是否有用戶覆寫規則"""
        # 檢查內容特徵覆寫
        content_hash = hash(content) % 10000
        if content_hash in self._user_overrides:
            mode = self._user_overrides[content_hash]
            return ModeDecision(
                mode=mode,
                confidence=1.0,
                reason="用戶指定模式覆寫",
                sensitivity_score=0.0,
            )
        
        # 檢查用戶級別覆寫
        if user_id and f"user:{user_id}" in self._user_overrides:
            mode = self._user_overrides[f"user:{user_id}"]
            return ModeDecision(
                mode=mode,
                confidence=1.0,
                reason=f"用戶 {user_id} 默認模式",
                sensitivity_score=0.0,
            )
        
        return None
    
    def _make_decision(
        self,
        score: float,
        analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> ModeDecision:
        """根據分數做出決策"""
        categories = analysis["categories"]
        
        # 高敏感度 → 強制本地
        if score >= self.local_threshold:
            return ModeDecision(
                mode=ExecutionMode.LOCAL_ONLY,
                confidence=0.95,
                reason=f"敏感度 {score:.2f} 超過本地閾值 {self.local_threshold}",
                sensitivity_score=score,
                requires_confirmation=True,
                suggested_actions=[
                    "建議使用本地模型處理",
                    "敏感數據將完全隔離",
                    "雲端僅接收脫敏後的元數據",
                ]
            )
        
        # 低敏感度 → 可用雲端
        if score <= self.cloud_threshold:
            return ModeDecision(
                mode=ExecutionMode.CLOUD_SANDBOX,
                confidence=0.85,
                reason=f"敏感度 {score:.2f} 低於雲端閾值 {self.cloud_threshold}",
                sensitivity_score=score,
                requires_confirmation=False,
                suggested_actions=[
                    "可使用雲端模型加速處理",
                    "數據已自動脫敏",
                ]
            )
        
        # 中間區域 → 混合模式（默認）
        return ModeDecision(
            mode=ExecutionMode.HYBRID,
            confidence=0.8,
            reason=f"使用默認混合模式（敏感度: {score:.2f}）",
            sensitivity_score=score,
            requires_confirmation=(score > 0.5),
            suggested_actions=[
                "雲端負責推理規劃",
                "本地執行實際操作",
                "最終結果本地覆寫",
            ]
        )
    
    def set_override(self, key: str, mode: ExecutionMode):
        """設置模式覆寫"""
        self._user_overrides[key] = mode
        logger.info(f"設置模式覆寫: {key} -> {mode.value}")
    
    def add_decision_hook(self, hook: Callable[[Dict], Optional[ModeDecision]]):
        """添加自定義決策鉤子"""
        self._decision_hooks.append(hook)
    
    def get_decision_explanation(self, decision: ModeDecision) -> str:
        """獲取決策解釋（用於用戶展示）"""
        lines = [
            f"🔒 執行模式: {decision.mode.value}",
            f"📊 敏感度評分: {decision.sensitivity_score:.2f}/1.0",
            f"🎯 置信度: {decision.confidence:.0%}",
            f"📝 決策原因: {decision.reason}",
        ]
        
        if decision.requires_confirmation:
            lines.append("⚠️  需要用戶確認")
        
        if decision.suggested_actions:
            lines.append("💡 建議操作:")
            for action in decision.suggested_actions:
                lines.append(f"   • {action}")
        
        return "\n".join(lines)
