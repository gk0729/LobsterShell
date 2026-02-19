"""
工具执行器 - LobsterShell 微内核核心

负责安全地执行工具，包括权限检查、超时控制、沙盒
"""

import asyncio
import time
from typing import Any, Dict, Optional
import logging

from ..interfaces.tool_interface import (
    ToolInterface,
    ToolContext,
    ToolResult,
    ToolConfig,
)
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    工具执行器
    
    安全地执行工具，提供：
    - 权限检查
    - 超时控制
    - 沙盒隔离
    - 审计日志
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        default_timeout: int = 30,
        enable_sandbox: bool = True,
    ):
        self.registry = registry
        self.default_timeout = default_timeout
        self.enable_sandbox = enable_sandbox
        self._audit_callback = None
    
    def set_audit_callback(self, callback):
        """设置审计回调"""
        self._audit_callback = callback
    
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
            timeout: 超时时间 (秒)
            
        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        
        # 1. 获取工具
        tool = self.registry.get_tool(tool_id)
        if not tool:
            return ToolResult(
                success=False,
                error=f"工具未找到: {tool_id}",
            )
        
        metadata = tool.metadata
        
        # 2. 权限检查
        if not tool.check_permission(context):
            missing_perms = set(metadata.permissions) - set(context.permissions)
            error_msg = f"权限不足，缺少: {missing_perms}"
            
            await self._audit(
                tool_id=tool_id,
                context=context,
                params=params,
                result=None,
                error=error_msg,
                time_ms=0,
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
            )
        
        # 3. 输入校验
        if not await tool.validate_input(params):
            return ToolResult(
                success=False,
                error="输入参数校验失败",
            )
        
        # 4. 执行 (带超时)
        timeout = timeout or metadata.input_schema.get("timeout", self.default_timeout)
        
        try:
            # 沙盒执行
            if self.enable_sandbox and metadata.sandbox_required:
                result = await self._execute_in_sandbox(
                    tool=tool,
                    context=context,
                    params=params,
                    timeout=timeout,
                )
            else:
                result = await self._execute_with_timeout(
                    tool=tool,
                    context=context,
                    params=params,
                    timeout=timeout,
                )
            
            # 5. 记录统计
            elapsed_ms = (time.time() - start_time) * 1000
            await self.registry.record_call(
                tool_id=tool_id,
                success=result.success,
                time_ms=elapsed_ms,
            )
            
            # 6. 审计
            await self._audit(
                tool_id=tool_id,
                context=context,
                params=params,
                result=result,
                error=None,
                time_ms=elapsed_ms,
            )
            
            return result
            
        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000
            await self.registry.record_call(tool_id, False, elapsed_ms)
            
            await self._audit(
                tool_id=tool_id,
                context=context,
                params=params,
                result=None,
                error=f"执行超时 ({timeout}s)",
                time_ms=elapsed_ms,
            )
            
            return ToolResult(
                success=False,
                error=f"工具执行超时 ({timeout} 秒)",
            )
        
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            await self.registry.record_call(tool_id, False, elapsed_ms)
            
            logger.exception(f"工具执行异常: {tool_id}")
            
            await self._audit(
                tool_id=tool_id,
                context=context,
                params=params,
                result=None,
                error=str(e),
                time_ms=elapsed_ms,
            )
            
            return ToolResult(
                success=False,
                error=f"执行异常: {str(e)}",
            )
    
    async def _execute_with_timeout(
        self,
        tool: ToolInterface,
        context: ToolContext,
        params: Dict[str, Any],
        timeout: int,
    ) -> ToolResult:
        """带超时执行"""
        return await asyncio.wait_for(
            tool.execute(context, params),
            timeout=timeout,
        )
    
    async def _execute_in_sandbox(
        self,
        tool: ToolInterface,
        context: ToolContext,
        params: Dict[str, Any],
        timeout: int,
    ) -> ToolResult:
        """
        在沙盒中执行
        
        TODO: 实现真正的沙盒隔离
        - Docker 容器
        - Firecracker VM
        - nsjail
        """
        # 目前只是带超时执行
        # TODO: 实现真正的沙盒
        return await self._execute_with_timeout(tool, context, params, timeout)
    
    async def _audit(
        self,
        tool_id: str,
        context: ToolContext,
        params: Dict[str, Any],
        result: Optional[ToolResult],
        error: Optional[str],
        time_ms: float,
    ):
        """审计记录"""
        if self._audit_callback:
            audit_data = {
                "tool_id": tool_id,
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "session_id": context.session_id,
                "request_id": context.request_id,
                "params": params,
                "success": result.success if result else False,
                "result_data": result.data if result and result.success else None,
                "error": error or (result.error if result else None),
                "time_ms": time_ms,
            }
            
            try:
                await self._audit_callback(audit_data)
            except Exception as e:
                logger.error(f"审计回调失败: {e}")
