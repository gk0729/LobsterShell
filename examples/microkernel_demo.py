"""
示例: 微内核架构使用

展示 LobsterShell 如何作为工具运行时，动态加载和执行工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lobstershell import (
    LobsterShell,
    ToolContext,
    Permission,
)


async def main():
    print("🦞 LobsterShell 微内核示例\n")
    
    # 1. 初始化 LobsterShell
    shell = LobsterShell(
        mode="hybrid_shield",
        enable_sandbox=True,
    )
    
    print("✅ LobsterShell 已初始化\n")
    
    # 2. 加载工具包
    tool_path = Path(__file__).parent.parent / "tools" / "lobster-tool-sql"
    
    if tool_path.exists():
        print(f"📦 加载工具包: {tool_path}\n")
        
        tool_ids = await shell.tools.load_directory(str(tool_path))
        
        print(f"已加载工具: {', '.join(tool_ids)}\n")
    else:
        print(f"⚠️  工具包不存在: {tool_path}")
        print("   请确保工具包目录存在\n")
        return
    
    # 3. 列出所有工具
    print("📋 已安装工具:")
    for tool_id in shell.tools.list():
        print(f"  • {tool_id}")
    print()
    
    # 4. 创建执行上下文
    context = ToolContext(
        user_id="user_001",
        tenant_id="tenant_default",
        mode="hybrid_shield",
        session_id="session_001",
        permissions=[Permission.DATABASE_READ],
        request_id="req_001",
    )
    
    # 5. 执行工具
    print("🔧 执行工具: sql.readonly_query\n")
    
    result = await shell.execute(
        tool_id="sql.readonly_query",
        context=context,
        params={
            "query": "SELECT 1 as test",
        },
    )
    
    print(f"执行结果:")
    print(f"  成功: {result.success}")
    if result.success:
        print(f"  数据: {result.data}")
        print(f"  元数据: {result.metadata}")
    else:
        print(f"  错误: {result.error}")
    print()
    
    # 6. 测试危险查询 (应该被拦截)
    print("🚫 测试危险查询 (DELETE):\n")
    
    result2 = await shell.execute(
        tool_id="sql.readonly_query",
        context=context,
        params={
            "query": "DELETE FROM users WHERE id=1",
        },
    )
    
    print(f"执行结果:")
    print(f"  成功: {result2.success}")
    print(f"  错误: {result2.error}")
    print()
    
    # 7. 查看统计
    print("📊 工具统计:")
    stats = shell.get_stats()
    print(f"  已加载工具: {stats['tools_loaded']}")
    print()
    
    # 8. 清理
    print("🧹 清理资源...")
    await shell.tools.unload("sql.readonly_query")
    print("✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
