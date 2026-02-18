"""
工具标准接口 - LobsterShell 微内核核心

所有工具必须实现此接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from enum import Enum


class Permission(str, Enum):
    """9层权限"""
    # 文件系统
    FILESYSTEM_READ = "filesystem:read"
    FILESYSTEM_WRITE = "filesystem:write"
    
    # 网络
    NETWORK_INTERNAL = "network:internal"
    NETWORK_EXTERNAL = "network:external"
    
    # 数据库
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"
    
    # 进程
    PROCESS_EXECUTE = "process:execute"
    
    # 系统
    SYSTEM_INFO = "system:info"
    SYSTEM_CONFIG = "system:config"


class ToolConfig(BaseModel):
    """工具配置"""
    enabled: bool = True
    permissions: List[Permission] = []
    rate_limit: Optional[int] = None  # 每分钟最大次数
    timeout: int = 30
    sandbox_enabled: bool = True


class ToolContext(BaseModel):
    """工具执行上下文"""
    user_id: str
    tenant_id: str
    mode: str  # local_only / hybrid_shield / cloud_sandbox
    session_id: str
    permissions: List[Permission]
    request_id: str


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ToolMetadata(BaseModel):
    """工具元数据"""
    id: str
    name: str
    description: str
    category: str  # database, web, file, code, crypto, messaging
    version: str = "1.0.0"
    author: str = "Unknown"
    license: str = "MIT"
    
    # 权限需求
    permissions: List[Permission] = []
    dangerous: bool = False
    
    # Schema
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    
    # 安全配置
    sandbox_required: bool = True
    network_access: bool = False
    filesystem_access: bool = False
    
    # 依赖
    dependencies: Dict[str, str] = {}  # {"python": ">=3.10", "packages": ["sqlalchemy"]}


class ToolInterface(ABC):
    """
    工具标准接口
    
    所有 LobsterShell 工具必须实现此接口
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """返回工具元数据"""
        pass
    
    @abstractmethod
    async def initialize(self, config: ToolConfig) -> bool:
        """
        初始化工具
        
        Args:
            config: 工具配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        context: ToolContext,
        params: Dict[str, Any]
    ) -> ToolResult:
        """
        执行工具
        
        Args:
            context: 执行上下文（用户、权限等）
            params: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        """
        校验输入参数
        
        Args:
            params: 输入参数
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    def check_permission(self, context: ToolContext) -> bool:
        """
        检查权限
        
        Args:
            context: 执行上下文
            
        Returns:
            bool: 是否有权限
        """
        required = set(self.metadata.permissions)
        granted = set(context.permissions)
        return required.issubset(granted)
