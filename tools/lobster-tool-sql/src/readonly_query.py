"""
SQL 只读查询工具 - LobsterShell 官方工具包

安全的只读 SQL 查询，自动拦截危险操作
"""

from typing import Any, Dict, List, Optional
import logging

# 从 lobstershell_core 导入接口
# 注意：实际使用时需要安装 lobstershell-core
try:
    from lobstershell_core.interfaces import (
        ToolInterface,
        ToolMetadata,
        ToolConfig,
        ToolContext,
        ToolResult,
        Permission,
    )
except ImportError:
    # 开发时使用相对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))
    from interfaces.tool_interface import (
        ToolInterface,
        ToolMetadata,
        ToolConfig,
        ToolContext,
        ToolResult,
        Permission,
    )

logger = logging.getLogger(__name__)


# 危险 SQL 关键词
DANGEROUS_KEYWORDS = {
    "DELETE", "UPDATE", "INSERT", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "MERGE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE",
}


class SQLReadOnlyQueryTool(ToolInterface):
    """SQL 只读查询工具"""
    
    def __init__(self):
        self._engine = None
        self._database_url = None
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="sql.readonly_query",
            name="SQL 只读查询",
            description="执行安全的只读 SQL 查询",
            category="database",
            version="1.0.0",
            author="LobsterShell Team",
            permissions=[Permission.DATABASE_READ],
            dangerous=False,
            sandbox_required=True,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "database": {"type": "string"},
                },
                "required": ["query"],
            },
        )
    
    async def initialize(self, config: ToolConfig) -> bool:
        """初始化数据库连接"""
        import os
        
        # 从环境变量获取数据库 URL
        self._database_url = os.environ.get("DATABASE_URL")
        
        if not self._database_url:
            logger.warning("DATABASE_URL 未设置，工具可能无法正常工作")
            return True  # 允许延迟初始化
        
        try:
            import sqlalchemy as sa
            self._engine = sa.create_engine(
                self._database_url,
                pool_size=5,
                max_overflow=10,
            )
            logger.info("✅ SQL 工具初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ SQL 工具初始化失败: {e}")
            return False
    
    async def execute(
        self,
        context: ToolContext,
        params: Dict[str, Any],
    ) -> ToolResult:
        """执行 SQL 查询"""
        query = params.get("query", "").strip()
        
        if not query:
            return ToolResult(
                success=False,
                error="查询语句不能为空",
            )
        
        # 1. 检查是否包含危险关键词
        query_upper = query.upper()
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                return ToolResult(
                    success=False,
                    error=f"⛔ 检测到危险 SQL 操作: {keyword}",
                )
        
        # 2. 检查是否为 SELECT 语句
        if not query_upper.startswith("SELECT"):
            return ToolResult(
                success=False,
                error="只允许 SELECT 查询",
            )
        
        # 3. 执行查询
        if not self._engine:
            return ToolResult(
                success=False,
                error="数据库未连接，请设置 DATABASE_URL",
            )
        
        try:
            import sqlalchemy as sa
            
            with self._engine.connect() as conn:
                result = conn.execute(sa.text(query))
                rows = [dict(row._mapping) for row in result]
            
            logger.info(f"✅ 查询成功，返回 {len(rows)} 行")
            
            return ToolResult(
                success=True,
                data={
                    "rows": rows,
                    "row_count": len(rows),
                },
                metadata={
                    "query": query,
                    "row_count": len(rows),
                },
            )
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return ToolResult(
                success=False,
                error=f"查询执行失败: {str(e)}",
            )
    
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        """校验输入参数"""
        query = params.get("query")
        return isinstance(query, str) and len(query.strip()) > 0
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("🗑️  SQL 工具资源已释放")


# 工具入口
Tool = SQLReadOnlyQueryTool
