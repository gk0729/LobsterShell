# 🦞 LobsterShell - 微内核 AI Agent 装甲

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Security: A+](https://img.shields.io/badge/security-A%2B-brightgreen.svg)]()

> **微内核架构** - 核心只有 ~2MB，工具按需安装

---

## 🎯 核心理念

```
❌ 旧模式 (单体内核)
LobsterShell {
  内置: 60+工具代码
  体积: ~50MB
  依赖: 全量安装
}

✅ 新模式 (微内核 + 插件化)
LobsterShell-Core {
  只包含: 工具运行时 + 权限引擎 + 沙盒
  体积: ~2MB
  依赖: 零
}
+
Tool Plugins {
  lobster-tool-sql: SQL 工具包
  lobster-tool-web: 网页抓取
  lobster-tool-file: 文件操作
  ... 按需安装
}
```

---

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│          LobsterShell Core (~2MB)        │
├─────────────────────────────────────────┤
│  • 工具运行时 (Loader/Registry/Executor) │
│  • 9 层权限引擎                          │
│  • 沙盒隔离器                            │
│  • 审计日志                              │
└───────────────┬─────────────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│ SQL   │   │ Web   │   │ File  │  ...
│ Tool  │   │ Tool  │   │ Tool  │
└───────┘   └───────┘   └───────┘
  可插拔      可插拔      可插拔
```

---

## 🚀 快速开始

### 1. 安装核心

```bash
pip install lobstershell-core
```

### 2. 安装工具包

```bash
# 搜索工具
lobster tool search sql

# 安装工具
lobster tool install lobster-tool-sql
```

### 3. 使用

```python
from lobstershell import LobsterShell, ToolContext, Permission

# 初始化
shell = LobsterShell()

# 加载工具
await shell.tools.load("lobster-tool-sql")

# 创建上下文
context = ToolContext(
    user_id="user_001",
    permissions=[Permission.DATABASE_READ],
    ...
)

# 执行
result = await shell.execute(
    tool_id="sql.readonly_query",
    context=context,
    params={"query": "SELECT * FROM users LIMIT 10"}
)
```

---

## 📦 官方工具包

| 工具包 | 说明 | 安装 |
|--------|------|------|
| `lobster-tool-sql` | 只读 SQL 查询 | `lobster tool install lobster-tool-sql` |
| `lobster-tool-web` | 网页抓取 | `lobster tool install lobster-tool-web` |
| `lobster-tool-file` | 文件操作 | `lobster tool install lobster-tool-file` |
| `lobster-tool-code` | 代码执行 | `lobster tool install lobster-tool-code` |

---

## 🔌 自定义工具

### 创建工具脚手架

```bash
lobster tool create my-custom-tool
```

### 工具接口

```python
from lobstershell import ToolInterface, ToolMetadata, ToolResult

class MyTool(ToolInterface):
    @property
    def metadata(self):
        return ToolMetadata(
            id="my.tool",
            name="我的工具",
            permissions=[Permission.NETWORK_INTERNAL],
        )
    
    async def execute(self, context, params):
        # 你的逻辑
        return ToolResult(success=True, data={...})
```

### 工具清单 (manifest.json)

```json
{
  "name": "my-custom-tool",
  "version": "1.0.0",
  "tools": [{
    "id": "my.tool",
    "permissions": ["network:internal"]
  }],
  "security": {
    "sandbox_required": true
  }
}
```

---

## 🔒 安全特性

### 9 层权限

```python
# 文件系统
filesystem:read
filesystem:write

# 网络
network:internal
network:external

# 数据库
database:read
database:write

# 进程
process:execute

# 系统
system:info
system:config
```

### 沙盒隔离

所有工具默认在沙盒中执行，隔离：
- 文件系统访问
- 网络访问
- 进程执行

### 审计日志

所有工具调用自动记录：
- 调用者信息
- 参数
- 结果
- 耗时

---

## 🎮 CLI 命令

```bash
# 搜索工具
lobster tool search <query>

# 安装工具
lobster tool install <package>

# 列出工具
lobster tool list

# 查看工具详情
lobster tool info <tool_id>

# 卸载工具
lobster tool uninstall <tool_id>

# 创建自定义工具
lobster tool create <tool_name>
```

---

## 📊 对比

| 维度 | 单体内核 | 微内核 |
|------|---------|--------|
| 核心体积 | ~50MB | ~2MB |
| 安装时间 | 2-3 分钟 | 10 秒 |
| 依赖冲突 | 高风险 | 按需隔离 |
| 自定义工具 | 修改源码 | 独立开发 |
| 安全审计 | 全量审计 | 单工具审计 |
| 更新粒度 | 全量更新 | 单工具更新 |

---

## 📂 项目结构

```
LobsterShell/
├── core/                      # 核心 (~2MB)
│   ├── interfaces/            # 工具接口定义
│   ├── tool_runtime/          # 工具运行时
│   │   ├── loader.py          # 工具加载器
│   │   ├── registry.py        # 工具注册中心
│   │   └── executor.py        # 工具执行器
│   └── security/              # 安全层
│
├── tools/                     # 官方工具包
│   └── lobster-tool-sql/      # SQL 工具
│       ├── manifest.json
│       └── src/readonly_query.py
│
├── cli/                       # CLI 工具
│   └── lobster_cli.py
│
└── examples/                  # 示例
    └── microkernel_demo.py
```

---

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 运行示例
python examples/microkernel_demo.py
```

---

## 📜 开源协议

MIT License

---

**口号**: 「让 AI 在云端思考，但工具在本地验证。」

**GitHub**: https://github.com/lobstershell/lobstershell
