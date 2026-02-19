#!/usr/bin/env python3
"""
LobsterShell CLI - 命令行工具

用法:
    lobster tool search <query>
    lobster tool install <package>
    lobster tool list
    lobster tool uninstall <tool_id>
    lobster tool info <tool_id>
"""

import asyncio
import click
import sys
from pathlib import Path

# 添加 core 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tool_runtime.loader import ToolLoader
from core.tool_runtime.registry import ToolRegistry


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🦞 LobsterShell - 微内核 AI Agent 装甲"""
    pass


@cli.group()
def tool():
    """工具管理"""
    pass


@tool.command("search")
@click.argument("query")
def search_tools(query: str):
    """搜索工具包"""
    click.echo(f"🔍 搜索工具: {query}")
    
    # TODO: 实现远程搜索
    # 目前只搜索已加载的工具
    registry = ToolRegistry()
    results = registry.search(query)
    
    if not results:
        click.echo("  未找到匹配的工具")
        return
    
    click.echo(f"\n找到 {len(results)} 个工具:")
    for tool_id in results:
        meta = registry.get_metadata(tool_id)
        if meta:
            click.echo(f"  • {tool_id}")
            click.echo(f"    {meta.name} - {meta.description}")
            click.echo(f"    类别: {meta.category} | 版本: {meta.version}")


@tool.command("install")
@click.argument("package")
@click.option("--local", "local_path", help="从本地目录安装")
def install_tool(package: str, local_path: Optional[str]):
    """安装工具包"""
    async def _install():
        loader = ToolLoader()
        
        try:
            if local_path:
                click.echo(f"📦 从本地安装: {local_path}")
                tool_ids = await loader.load_from_directory(local_path)
            else:
                click.echo(f"⬇️  从 pip 安装: {package}")
                tool_ids = await loader.load_from_pip(package)
            
            click.echo(f"\n✅ 安装成功!")
            click.echo(f"已加载工具: {', '.join(tool_ids)}")
            
        except Exception as e:
            click.echo(f"❌ 安装失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_install())


@tool.command("list")
def list_tools():
    """列出已安装的工具"""
    registry = ToolRegistry()
    tools = registry.list_tools()
    
    if not tools:
        click.echo("📋 未安装任何工具")
        return
    
    click.echo(f"📋 已安装工具 ({len(tools)} 个):\n")
    
    # 按类别分组
    categories = {}
    for tool_id in tools:
        meta = registry.get_metadata(tool_id)
        if meta:
            cat = meta.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((tool_id, meta))
    
    for category, tool_list in sorted(categories.items()):
        click.echo(f"  [{category}]")
        for tool_id, meta in tool_list:
            dangerous = "⚠️ " if meta.dangerous else "  "
            click.echo(f"  {dangerous}{tool_id} - {meta.name}")
        click.echo()


@tool.command("info")
@click.argument("tool_id")
def tool_info(tool_id: str):
    """查看工具详情"""
    registry = ToolRegistry()
    meta = registry.get_metadata(tool_id)
    
    if not meta:
        click.echo(f"❌ 工具未找到: {tool_id}", err=True)
        sys.exit(1)
    
    click.echo(f"\n📦 {tool_id}\n")
    click.echo(f"  名称: {meta.name}")
    click.echo(f"  描述: {meta.description}")
    click.echo(f"  类别: {meta.category}")
    click.echo(f"  版本: {meta.version}")
    click.echo(f"  作者: {meta.author}")
    click.echo(f"  许可: {meta.license}")
    
    click.echo(f"\n  权限需求:")
    for perm in meta.permissions:
        click.echo(f"    • {perm.value}")
    
    click.echo(f"\n  危险等级: {'⚠️  危险' if meta.dangerous else '✅ 安全'}")
    click.echo(f"  沙盒要求: {'是' if meta.sandbox_required else '否'}")


@tool.command("uninstall")
@click.argument("tool_id")
@click.confirmation_option(prompt="确认卸载?")
def uninstall_tool(tool_id: str):
    """卸载工具"""
    async def _uninstall():
        loader = ToolLoader()
        
        success = await loader.unload_tool(tool_id)
        
        if success:
            click.echo(f"✅ 已卸载: {tool_id}")
        else:
            click.echo(f"❌ 卸载失败: {tool_id}", err=True)
            sys.exit(1)
    
    asyncio.run(_uninstall())


@tool.command("create")
@click.argument("tool_name")
def create_tool(tool_name: str):
    """创建自定义工具脚手架"""
    import os
    
    tool_dir = Path(tool_name)
    
    if tool_dir.exists():
        click.echo(f"❌ 目录已存在: {tool_name}", err=True)
        sys.exit(1)
    
    # 创建目录结构
    (tool_dir / "src").mkdir(parents=True)
    (tool_dir / "tests").mkdir(parents=True)
    
    # manifest.json
    manifest = {
        "name": tool_name,
        "version": "0.1.0",
        "author": "Your Name",
        "license": "MIT",
        "description": "自定义工具",
        "tools": [{
            "id": f"{tool_name}.main",
            "name": "主工具",
            "module": "main",
            "class": "Tool",
            "category": "custom",
            "permissions": [],
        }],
        "dependencies": {"python": ">=3.10", "packages": []},
        "security": {
            "sandbox_required": False,
            "network_access": False,
            "filesystem_access": False,
        },
    }
    
    import json
    with open(tool_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # src/main.py
    main_py = f'''"""
{tool_name} - 自定义工具
"""

from lobstershell_core.interfaces import (
    ToolInterface,
    ToolMetadata,
    ToolConfig,
    ToolContext,
    ToolResult,
)


class Tool(ToolInterface):
    @property
    def metadata(self):
        return ToolMetadata(
            id="{tool_name}.main",
            name="主工具",
            description="自定义工具",
            category="custom",
        )
    
    async def initialize(self, config: ToolConfig):
        return True
    
    async def execute(self, context: ToolContext, params: dict):
        # TODO: 实现你的工具逻辑
        return ToolResult(
            success=True,
            data={{"message": "Hello from {tool_name}!"}},
        )
    
    async def validate_input(self, params: dict):
        return True
    
    async def cleanup(self):
        pass
'''
    
    with open(tool_dir / "src" / "main.py", "w") as f:
        f.write(main_py)
    
    # README.md
    readme = f'''# {tool_name}

自定义 LobsterShell 工具

## 安装

```bash
lobster tool install --local ./{tool_name}
```

## 使用

```python
result = await shell.execute_tool(
    tool_id="{tool_name}.main",
    params={{}}
)
```
'''
    
    with open(tool_dir / "README.md", "w") as f:
        f.write(readme)
    
    click.echo(f"✅ 已创建工具脚手架: {tool_name}/")
    click.echo(f"\n目录结构:")
    click.echo(f"  {tool_name}/")
    click.echo(f"  ├── manifest.json")
    click.echo(f"  ├── src/")
    click.echo(f"  │   └── main.py")
    click.echo(f"  ├── tests/")
    click.echo(f"  └── README.md")
    click.echo(f"\n下一步:")
    click.echo(f"  1. 编辑 src/main.py 实现你的工具")
    click.echo(f"  2. lobster tool install --local ./{tool_name}")


if __name__ == "__main__":
    cli()
