"""
工具注册中心 - LobsterShell 微内核核心

管理所有已注册工具的元数据和实例
"""

from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime

from ..interfaces.tool_interface import ToolInterface, ToolMetadata

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册中心
    
    线程安全的工具注册表
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolInterface] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._stats: Dict[str, dict] = {}  # 工具使用统计
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        tool_id: str,
        tool: ToolInterface,
        manifest: Optional[dict] = None,
    ) -> bool:
        """
        注册工具
        
        Args:
            tool_id: 工具 ID
            tool: 工具实例
            manifest: 工具清单 (可选，用于存储额外信息)
            
        Returns:
            bool: 是否注册成功
        """
        async with self._lock:
            if tool_id in self._tools:
                logger.warning(f"工具已存在，将覆盖: {tool_id}")
            
            self._tools[tool_id] = tool
            self._metadata[tool_id] = tool.metadata
            self._stats[tool_id] = {
                "registered_at": datetime.utcnow(),
                "call_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_time_ms": 0,
            }
            
            logger.debug(f"注册工具: {tool_id}")
            return True
    
    async def unregister(self, tool_id: str) -> bool:
        """
        注销工具
        
        Args:
            tool_id: 工具 ID
            
        Returns:
            bool: 是否注销成功
        """
        async with self._lock:
            if tool_id not in self._tools:
                return False
            
            del self._tools[tool_id]
            del self._metadata[tool_id]
            # 保留统计数据
            
            logger.debug(f"注销工具: {tool_id}")
            return True
    
    def get_tool(self, tool_id: str) -> Optional[ToolInterface]:
        """获取工具实例"""
        return self._tools.get(tool_id)
    
    def get_metadata(self, tool_id: str) -> Optional[ToolMetadata]:
        """获取工具元数据"""
        return self._metadata.get(tool_id)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        列出所有工具
        
        Args:
            category: 按类别过滤 (可选)
            
        Returns:
            List[str]: 工具 ID 列表
        """
        if not category:
            return list(self._tools.keys())
        
        return [
            tool_id
            for tool_id, meta in self._metadata.items()
            if meta.category == category
        ]
    
    def list_categories(self) -> List[str]:
        """列出所有工具类别"""
        categories = set()
        for meta in self._metadata.values():
            categories.add(meta.category)
        return list(categories)
    
    def search(self, query: str) -> List[str]:
        """
        搜索工具
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[str]: 匹配的工具 ID 列表
        """
        query_lower = query.lower()
        results = []
        
        for tool_id, meta in self._metadata.items():
            # 在 ID、名称、描述中搜索
            if (
                query_lower in tool_id.lower()
                or query_lower in meta.name.lower()
                or query_lower in meta.description.lower()
            ):
                results.append(tool_id)
        
        return results
    
    async def record_call(
        self,
        tool_id: str,
        success: bool,
        time_ms: float,
    ):
        """记录工具调用"""
        if tool_id not in self._stats:
            return
        
        async with self._lock:
            self._stats[tool_id]["call_count"] += 1
            if success:
                self._stats[tool_id]["success_count"] += 1
            else:
                self._stats[tool_id]["error_count"] += 1
            self._stats[tool_id]["total_time_ms"] += time_ms
    
    def get_stats(self, tool_id: str) -> Optional[dict]:
        """获取工具统计信息"""
        return self._stats.get(tool_id)
    
    def get_all_stats(self) -> Dict[str, dict]:
        """获取所有工具统计"""
        return self._stats.copy()
    
    def export_metadata(self) -> List[dict]:
        """导出所有工具元数据 (用于 API)"""
        return [
            {
                "id": tool_id,
                "name": meta.name,
                "description": meta.description,
                "category": meta.category,
                "version": meta.version,
                "permissions": [p.value for p in meta.permissions],
                "dangerous": meta.dangerous,
            }
            for tool_id, meta in self._metadata.items()
        ]
