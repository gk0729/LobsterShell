"""
🦞 Soul Core - LobsterShell 靈魂核心
======================================
整合所有核心組件，提供統一的執行入口

執行流程:
    輸入 → 敏感度分析 → 模式決策 → 安全檢查 → 執行 → 數據覆寫 → 審計

核心價值:
1. 主動感知：自動分析輸入風險
2. 動態決策：根據風險選擇執行模式
3. 分層防護：多階段安全檢查
4. 零幻覺輸出：精確數據覆寫
5. 全程審計：不可篡改的執行記錄
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import uuid
import time
import logging

from .dynamic_mode_engine import DynamicModeEngine, ExecutionMode, ModeDecision
from .layered_security import LayeredSecuritySystem, SecurityPhase, SecurityReport
from .zero_hallucination_overwriter import ZeroHallucinationOverwriter, OverwriteRule, DataSource
from .audit_chain import AuditChain, AuditEntry, AuditLevel, AuditEventType

logger = logging.getLogger(__name__)


class ExecutionStage(Enum):
    """執行階段"""
    INIT = "init"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    SECURITY_CHECK = "security_check"
    EXECUTING = "executing"
    OVERWRITING = "overwriting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """執行上下文"""
    # 請求識別
    request_id: str
    session_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # 輸入
    input_content: str = ""
    input_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 權限
    granted_permissions: List[str] = field(default_factory=list)
    
    # 用戶偏好
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # 追蹤
    start_time: float = field(default_factory=time.time)
    stage: ExecutionStage = ExecutionStage.INIT


@dataclass
class ExecutionResult:
    """執行結果"""
    # 狀態
    success: bool
    request_id: str
    
    # 決策
    mode: ExecutionMode
    mode_decision: ModeDecision
    
    # 輸出
    output: str = ""
    output_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 安全
    security_report: Optional[SecurityReport] = None
    
    # 覆寫
    overwrite_stats: Optional[Dict[str, Any]] = None
    
    # 性能
    total_time_ms: float = 0.0
    stage_timings: Dict[str, float] = field(default_factory=dict)
    
    # 錯誤
    error: Optional[str] = None
    error_stage: Optional[ExecutionStage] = None


class SoulCore:
    """
    LobsterShell 靈魂核心
    
    這是整個架構的指揮中心，協調所有組件完成一次安全的 AI 執行。
    
    使用示例:
        core = SoulCore()
        
        context = ExecutionContext(
            request_id="req-001",
            session_id="sess-001",
            user_id="user-001",
            input_content="查詢我的餘額",
        )
        
        result = await core.execute(context)
        print(result.output)
    """
    
    def __init__(
        self,
        local_threshold: float = 0.8,
        cloud_threshold: float = 0.3,
        enable_audit: bool = True,
        fail_fast_security: bool = True,
    ):
        # 初始化各組件
        self.mode_engine = DynamicModeEngine(
            local_threshold=local_threshold,
            cloud_threshold=cloud_threshold,
        )
        
        self.security_system = LayeredSecuritySystem(
            fail_fast=fail_fast_security,
        )
        
        self.overwriter = ZeroHallucinationOverwriter()
        
        self.audit_chain = AuditChain() if enable_audit else None
        
        # 執行器註冊表
        self._executors: Dict[ExecutionMode, Callable] = {}
        
        # 統計
        self._stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "by_mode": {},
        }
        
        logger.info("🦞 SoulCore 初始化完成")
    
    def register_executor(self, mode: ExecutionMode, executor: Callable):
        """註冊特定模式的執行器"""
        self._executors[mode] = executor
        logger.info(f"註冊執行器: {mode.value}")
    
    def register_data_source(self, source: DataSource):
        """註冊數據源"""
        self.overwriter.register_data_source(source)
    
    def register_overwrite_rule(self, rule: OverwriteRule):
        """註冊覆寫規則"""
        self.overwriter.register_rule(rule)
    
    async def execute(
        self,
        context: ExecutionContext,
        skip_security: bool = False,
        skip_overwrite: bool = False,
    ) -> ExecutionResult:
        """
        執行一次完整的 AI 請求處理
        
        這是核心的「主動思考動態解決問題」流程：
        1. 主動感知輸入風險
        2. 動態決策執行模式
        3. 分層安全檢查
        4. 模式特定執行
        5. 零幻覺數據覆寫
        6. 完整審計記錄
        """
        timings = {}
        stage_start = time.time()
        
        try:
            # === Stage 1: 敏感度分析 ===
            context.stage = ExecutionStage.ANALYZING
            decision = self.mode_engine.decide(
                content=context.input_content,
                user_id=context.user_id,
                context={
                    "user_preferences": context.user_preferences,
                    "is_admin": "admin" in context.granted_permissions,
                },
            )
            timings["analyze"] = (time.time() - stage_start) * 1000
            
            self._audit(
                event_type=AuditEventType.MODE_DECISION,
                action="mode_decision",
                description=f"選擇執行模式: {decision.mode.value}",
                context=context,
                decision=decision.mode.value,
                reason=decision.reason,
                confidence=decision.confidence,
            )
            
            # 如果需要用戶確認
            if decision.requires_confirmation:
                logger.warning(f"執行需要確認: {context.request_id}")
                # TODO: 實現用戶確認流程
            
            # === Stage 2: 安全檢查 ===
            stage_start = time.time()
            context.stage = ExecutionStage.SECURITY_CHECK
            
            security_report = None
            if not skip_security:
                security_context = {
                    "user_id": context.user_id,
                    "content": context.input_content,
                    "granted_permissions": context.granted_permissions,
                    "required_permissions": self._get_required_permissions(decision.mode),
                }
                
                security_report = self.security_system.run_all(security_context)
                timings["security"] = (time.time() - stage_start) * 1000
                
                # 記錄安全檢查結果
                self._audit(
                    event_type=AuditEventType.SECURITY_CHECK,
                    action="security_check",
                    description=f"安全檢查完成: {security_report.risk_level}",
                    context=context,
                    success=security_report.overall_passed,
                    details={
                        "risk_level": security_report.risk_level,
                        "phase_summary": security_report.phase_summary,
                    },
                )
                
                # 關鍵安全問題直接拒絕
                if security_report.risk_level == "critical":
                    return ExecutionResult(
                        success=False,
                        request_id=context.request_id,
                        mode=decision.mode,
                        mode_decision=decision,
                        security_report=security_report,
                        error="安全檢查未通過（關鍵風險）",
                        error_stage=ExecutionStage.SECURITY_CHECK,
                        total_time_ms=sum(timings.values()),
                        stage_timings=timings,
                    )
            
            # === Stage 3: 執行（模式特定）===
            stage_start = time.time()
            context.stage = ExecutionStage.EXECUTING
            
            executor = self._executors.get(decision.mode)
            if not executor:
                raise ValueError(f"未找到模式 {decision.mode.value} 的執行器")
            
            self._audit(
                event_type=AuditEventType.EXECUTION_START,
                action="execution_start",
                description=f"開始執行: {decision.mode.value}",
                context=context,
            )
            
            # 執行
            raw_output = await executor(context, decision)
            timings["execute"] = (time.time() - stage_start) * 1000
            
            self._audit(
                event_type=AuditEventType.EXECUTION_END,
                action="execution_end",
                description="執行完成",
                context=context,
                success=True,
            )
            
            # === Stage 4: 數據覆寫（零幻覺）===
            stage_start = time.time()
            context.stage = ExecutionStage.OVERWRITING
            
            final_output = raw_output
            overwrite_stats = None
            
            if not skip_overwrite:
                overwrite_result = await self.overwriter.overwrite(
                    template=raw_output,
                    context={
                        "user_id": context.user_id,
                        "request_id": context.request_id,
                    },
                )
                final_output = overwrite_result["final_output"]
                overwrite_stats = overwrite_result["stats"]
                timings["overwrite"] = (time.time() - stage_start) * 1000
                
                self._audit(
                    event_type=AuditEventType.DATA_OVERWRITE,
                    action="data_overwrite",
                    description=f"數據覆寫完成: {overwrite_stats}",
                    context=context,
                    success=overwrite_result["success"],
                    details={"stats": overwrite_stats},
                )
            
            # === 完成 ===
            context.stage = ExecutionStage.COMPLETED
            total_time = (time.time() - context.start_time) * 1000
            
            self._update_stats(decision.mode, success=True)
            
            return ExecutionResult(
                success=True,
                request_id=context.request_id,
                mode=decision.mode,
                mode_decision=decision,
                output=final_output,
                security_report=security_report,
                overwrite_stats=overwrite_stats,
                total_time_ms=total_time,
                stage_timings=timings,
            )
            
        except Exception as e:
            logger.exception(f"執行失敗: {context.request_id}")
            
            self._audit(
                event_type=AuditEventType.EXECUTION_END,
                action="execution_failed",
                description=f"執行失敗: {str(e)}",
                context=context,
                success=False,
                level=AuditLevel.ERROR,
            )
            
            self._update_stats(decision.mode if 'decision' in locals() else ExecutionMode.HYBRID, success=False)
            
            return ExecutionResult(
                success=False,
                request_id=context.request_id,
                mode=decision.mode if 'decision' in locals() else ExecutionMode.HYBRID,
                mode_decision=decision if 'decision' in locals() else None,
                error=str(e),
                error_stage=context.stage,
                total_time_ms=(time.time() - context.start_time) * 1000,
                stage_timings=timings,
            )
    
    def _audit(
        self,
        event_type: AuditEventType,
        action: str,
        description: str,
        context: ExecutionContext,
        success: bool = True,
        level: AuditLevel = AuditLevel.INFO,
        **kwargs,
    ):
        """記錄審計日誌"""
        if not self.audit_chain:
            return
        
        self.audit_chain.create_entry(
            event_type=event_type,
            action=action,
            description=description,
            session_id=context.session_id,
            request_id=context.request_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            level=level,
            success=success,
            **kwargs,
        )
    
    def _get_required_permissions(self, mode: ExecutionMode) -> List[str]:
        """獲取模式所需的權限"""
        base_permissions = ["ai:use"]
        
        if mode == ExecutionMode.CLOUD_SANDBOX:
            base_permissions.append("ai:cloud")
        
        if mode == ExecutionMode.LOCAL_ONLY:
            base_permissions.append("ai:local")
        
        return base_permissions
    
    def _update_stats(self, mode: ExecutionMode, success: bool):
        """更新統計"""
        self._stats["total_executions"] += 1
        
        if success:
            self._stats["successful"] += 1
        else:
            self._stats["failed"] += 1
        
        mode_str = mode.value
        if mode_str not in self._stats["by_mode"]:
            self._stats["by_mode"][mode_str] = {"total": 0, "success": 0}
        
        self._stats["by_mode"][mode_str]["total"] += 1
        if success:
            self._stats["by_mode"][mode_str]["success"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取執行統計"""
        stats = self._stats.copy()
        
        # 計算成功率
        if stats["total_executions"] > 0:
            stats["success_rate"] = stats["successful"] / stats["total_executions"]
        
        # 審計鏈統計
        if self.audit_chain:
            stats["audit"] = self.audit_chain.get_stats()
        
        return stats
    
    def get_audit_report(self, session_id: Optional[str] = None) -> str:
        """獲取審計報告"""
        if not self.audit_chain:
            return "審計功能未啟用"
        
        return self.audit_chain.generate_report(session_id)
    
    def verify_audit_chain(self) -> bool:
        """驗證審計鏈完整性"""
        if not self.audit_chain:
            return True
        
        status = self.audit_chain.verify_chain()
        return status.valid
