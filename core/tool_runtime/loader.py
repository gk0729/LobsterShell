"""
工具动态加载器 - LobsterShell 微内核核心

负责动态加载、卸载、管理工具插件
"""

import importlib
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from ..interfaces.tool_interface import ToolInterface, ToolMetadata, ToolConfig
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """安全检查失败"""
    pass


class DependencyError(Exception):
    """依赖检查失败"""
    pass


class ToolLoader:
    """
    工具动态加载器
    
    支持从本地目录、pip 包、远程仓库加载工具
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()
        self.loaded_tools: Dict[str, ToolInterface] = {}
        self._tool_packages: Dict[str, Path] = {}  # tool_id -> package_path
    
    async def load_from_directory(
        self,
        package_path: str,
        config: Optional[ToolConfig] = None,
    ) -> List[str]:
        """
        从目录加载工具包
        
        Args:
            package_path: 工具包目录路径
            config: 工具配置
            
        Returns:
            List[str]: 已加载的工具 ID 列表
        """
        package_dir = Path(package_path)
        manifest_path = package_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise ValueError(f"未找到 manifest.json: {package_path}")
        
        # 1. 读取清单
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        logger.info(f"📦 加载工具包: {manifest['name']}@{manifest.get('version', 'unknown')}")
        
        # 2. 安全检查
        if not await self._security_check(manifest):
            raise SecurityError(f"工具包安全检查失败: {manifest['name']}")
        
        # 3. 依赖检查
        if not await self._dependency_check(manifest):
            raise DependencyError(f"依赖项缺失: {manifest.get('dependencies', {})}")
        
        # 4. 加载所有工具
        loaded_tool_ids = []
        for tool_def in manifest.get("tools", []):
            tool_id = tool_def["id"]
            
            try:
                # 动态导入工具类
                tool_class = self._import_tool_class(package_dir, tool_def)
                
                # 实例化
                tool_instance = tool_class()
                
                # 初始化
                tool_config = config or ToolConfig()
                if not await tool_instance.initialize(tool_config):
                    logger.error(f"❌ 工具初始化失败: {tool_id}")
                    continue
                
                # 注册
                await self.registry.register(tool_id, tool_instance)
                self.loaded_tools[tool_id] = tool_instance
                self._tool_packages[tool_id] = package_dir
                
                loaded_tool_ids.append(tool_id)
                logger.info(f"  ✅ 已加载: {tool_id}")
                
            except Exception as e:
                logger.error(f"  ❌ 加载失败 {tool_id}: {e}")
                continue
        
        return loaded_tool_ids
    
    async def load_from_pip(
        self,
        package_name: str,
        config: Optional[ToolConfig] = None,
    ) -> List[str]:
        """
        从 pip 包加载工具
        
        Args:
            package_name: pip 包名 (e.g., "lobster-tool-sql")
            config: 工具配置
            
        Returns:
            List[str]: 已加载的工具 ID 列表
        """
        import subprocess
        import sys
        
        # 1. 安装包
        logger.info(f"⬇️  安装 {package_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"安装失败: {result.stderr}")
        
        # 2. 查找包路径
        try:
            import importlib.util
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                raise ValueError(f"找不到包: {package_name}")
            
            package_dir = Path(spec.origin).parent
            return await self.load_from_directory(str(package_dir), config)
            
        except ImportError as e:
            raise ImportError(f"无法导入包: {package_name}") from e
    
    async def unload_tool(self, tool_id: str) -> bool:
        """
        卸载工具
        
        Args:
            tool_id: 工具 ID
            
        Returns:
            bool: 是否成功卸载
        """
        if tool_id not in self.loaded_tools:
            logger.warning(f"工具未加载: {tool_id}")
            return False
        
        try:
            # 清理资源
            await self.loaded_tools[tool_id].cleanup()
            
            # 从注册表移除
            await self.registry.unregister(tool_id)
            
            # 移除引用
            del self.loaded_tools[tool_id]
            if tool_id in self._tool_packages:
                del self._tool_packages[tool_id]
            
            logger.info(f"🗑️  已卸载: {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"卸载失败 {tool_id}: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[ToolInterface]:
        """获取已加载的工具"""
        return self.loaded_tools.get(tool_id)
    
    def list_loaded_tools(self) -> List[str]:
        """列出所有已加载的工具"""
        return list(self.loaded_tools.keys())
    
    def _import_tool_class(
        self,
        package_dir: Path,
        tool_def: dict,
    ) -> Type[ToolInterface]:
        """动态导入工具类"""
        import sys
        
        module_path = tool_def.get("module", "main")
        class_name = tool_def.get("class", "Tool")
        
        # 添加到 sys.path
        src_dir = package_dir / "src"
        if src_dir.exists():
            sys.path.insert(0, str(src_dir))
        else:
            sys.path.insert(0, str(package_dir))
        
        # 动态导入
        module = importlib.import_module(module_path)
        tool_class = getattr(module, class_name)
        
        return tool_class
    
    async def _security_check(self, manifest: dict) -> bool:
        """
        安全检查
        
        检查权限声明是否合理
        """
        # 提取所有权限需求
        required_perms = set()
        for tool in manifest.get("tools", []):
            required_perms.update(tool.get("permissions", []))
        
        # 危险权限列表
        dangerous_perms = {
            "filesystem:write",
            "network:external",
            "process:execute",
            "database:write",
            "system:config",
        }
        
        # 如果包含危险权限，需要额外验证
        if required_perms & dangerous_perms:
            logger.warning(f"⚠️  工具包包含危险权限: {required_perms & dangerous_perms}")
            # TODO: 实现更严格的安全检查
            # - 代码静态分析
            # - 签名验证
            # - 用户确认
        
        return True
    
    async def _dependency_check(self, manifest: dict) -> bool:
        """
        依赖检查
        
        检查 Python 版本、必需包等
        """
        import sys
        from packaging import version
        
        deps = manifest.get("dependencies", {})
        
        # 检查 Python 版本
        python_req = deps.get("python")
        if python_req:
            # 简单检查 (TODO: 使用 packaging 解析版本范围)
            if python_req.startswith(">="):
                min_version = python_req[2:]
                if version.parse(sys.version.split()[0]) < version.parse(min_version):
                    logger.error(f"❌ Python 版本不满足: {python_req}")
                    return False
        
        # 检查必需包
        packages = deps.get("packages", [])
        for pkg in packages:
            try:
                importlib.import_module(pkg.split("[")[0].split(">")[0].split("<")[0])
            except ImportError:
                logger.warning(f"⚠️  缺少依赖: {pkg}")
                # 不阻止加载，只警告
                # TODO: 自动安装依赖
        
        return True
