"""
LobsterShell - 微内核 AI Agent 装甲

核心 (~2MB) + 可插拔工具生态

用法:
    from lobstershell import LobsterShell
    
    shell = LobsterShell()
    await shell.tools.load("lobster-tool-sql")
    
    result = await shell.execute(
        tool_id="sql.readonly_query",
        params={"query": "SELECT * FROM users LIMIT 10"}
    )
"""

from typing import Any, Dict, List, Optional
import logging
from importlib import import_module

# 核心组件
from .core.interfaces.tool_interface import (
    ToolInterface,
    ToolMetadata,
    ToolConfig,
    ToolContext,
    ToolResult,
    Permission,
)
from .core.tool_runtime.loader import ToolLoader
from .core.tool_runtime.registry import ToolRegistry
from .core.tool_runtime.executor import ToolExecutor

# 旧版兼容
_mode_controller = import_module(".00_core.mode_controller", __name__)
ModeController = _mode_controller.ModeController
ModeConfig = _mode_controller.ModeConfig
PolicyEngine = import_module(".00_core.policy_engine", __name__).PolicyEngine
_audit_logger_module = import_module(".00_core.audit_logger", __name__)
AuditLogger = _audit_logger_module.AuditLogger
AuditLevel = _audit_logger_module.AuditLevel

__version__ = "0.2.0"
__author__ = "LobsterShell Team"

__all__ = [
    # 主类
    "LobsterShell",
    # 工具接口
    "ToolInterface",
    "ToolMetadata",
    "ToolConfig",
    "ToolContext",
    "ToolResult",
    "Permission",
    # 运行时组件
    "ToolLoader",
    "ToolRegistry",
    "ToolExecutor",
    # 旧版兼容
    "ModeController",
    "ModeConfig",
    "PolicyEngine",
    "AuditLogger",
]

logger = logging.getLogger(__name__)


class ToolsManager:
    """工具管理器"""
    
    def __init__(self, shell: "LobsterShell"):
        self.shell = shell
        self.loader = ToolLoader(registry=shell.registry)
    
    async def load(self, package: str, local_path: Optional[str] = None):
        """加载工具包"""
        if local_path:
            return await self.loader.load_from_directory(local_path)
        else:
            return await self.loader.load_from_pip(package)
    
    async def load_directory(self, path: str):
        """从目录加载"""
        return await self.loader.load_from_directory(path)
    
    def list(self) -> List[str]:
        """列出已加载工具"""
        return self.shell.registry.list_tools()
    
    def get(self, tool_id: str) -> Optional[ToolInterface]:
        """获取工具"""
        return self.loader.get_tool(tool_id)
    
    async def unload(self, tool_id: str):
        """卸载工具"""
        return await self.loader.unload_tool(tool_id)


class LobsterShell:
    """
    LobsterShell 微内核
    
    用法:
        shell = LobsterShell()
        
        # 加载工具
        await shell.tools.load_directory("./tools/lobster-tool-sql")
        
        # 执行工具
        result = await shell.execute(
            tool_id="sql.readonly_query",
            context=context,
            params={"query": "SELECT 1"}
        )
    """
    
    def __init__(
        self,
        mode: ModeConfig = ModeConfig.HYBRID_SHIELD,
        enable_sandbox: bool = True,
        audit_enabled: bool = True,
    ):
        """
        初始化 LobsterShell
        
        Args:
            mode: 安全模式
            enable_sandbox: 是否启用沙盒
            audit_enabled: 是否启用审计
        """
        self.mode = mode
        self.enable_sandbox = enable_sandbox
        
        # 核心组件
        self.registry = ToolRegistry()
        self.executor = ToolExecutor(
            registry=self.registry,
            enable_sandbox=enable_sandbox,
        )
        
        # 工具管理
        self.tools = ToolsManager(self)
        
        # 旧版组件 (兼容)
        self.mode_controller = ModeController(default_mode=mode)
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger() if audit_enabled else None
        
        # 设置审计回调
        if self.audit_logger:
            self.executor.set_audit_callback(self._audit_callback)
        
        logger.info(f"🦞 LobsterShell 初始化完成 (mode={mode.value})")
    
    async def execute(
        self,
        tool_id: str,
        context: ToolContext,
        params: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_id: 工具 ID
            context: 执行上下文
            params: 工具参数
            timeout: 超时时间
            
        Returns:
            ToolResult: 执行结果
        """
        return await self.executor.execute(
            tool_id=tool_id,
            context=context,
            params=params,
            timeout=timeout,
        )
    
    async def _audit_callback(self, audit_data: dict):
        """审计回调"""
        if self.audit_logger:
            self.audit_logger.log(
                action=audit_data["tool_id"],
                level=AuditLevel.INFO if audit_data["success"] else AuditLevel.WARNING,
                user_id=audit_data["user_id"],
                session_id=audit_data["session_id"],
                request=audit_data.get("params"),
                response=audit_data.get("result_data"),
                local_review_result={
                    "success": audit_data["success"],
                    "time_ms": audit_data["time_ms"],
                },
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "tools_loaded": len(self.tools.list()),
            "registry": self.registry.export_metadata(),
            "tool_stats": self.registry.get_all_stats(),
        }
