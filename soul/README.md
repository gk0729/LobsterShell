# LobsterShell Soul - OpenClaw 集成

**AI 安全灵魂层 - 主動思考動態解決問題**

## 概述

LobsterShell Soul 是一个可以嵌入任何 AI 系统的安全层，提供：

- 🎯 **主动感知**：自动分析输入风险级别 (0-1)
- ⚡ **动态决策**：根据风险选择执行模式 (Local/Hybrid/Cloud)
- 🛡️ **四阶段防护**：Fail-Fast 安全检查
- ✨ **零幻觉输出**：AI 模板 + SQL 精确数据覆写
- 📜 **不可篡改审计**：哈希链确保完整性

## 与 OpenClaw 的关系

### OpenClaw (当前)
```
用户 → Gateway → Agent → Tools → 输出
```

### OpenClaw + LobsterShell Soul (增强后)
```
用户
  ↓
【前置】LobsterShell Soul
  ├─ 敏感度分析
  ├─ 动态模式决策
  └─ 安全检查
  ↓
Gateway → Agent → Tools
  ↓
【后置】LobsterShell Soul
  ├─ 零幻觉覆写
  └─ 审计记录
  ↓
输出
```

## 快速开始

### 1. 复制到你的项目

```bash
cp -r integrations/lobstershell-soul/soul_architecture /your/project/
```

### 2. Python 直接使用

```python
from soul_architecture import SoulCore, ExecutionContext
import asyncio

async def main():
    # 初始化
    core = SoulCore()

    # 执行
    context = ExecutionContext(
        request_id="req-001",
        input_content="查询余额",
    )
    result = await core.execute(context)
    print(result.output)

asyncio.run(main())
```

### 3. 与 OpenClaw 集成（开发中）

```typescript
// 未来集成方式
import { SoulMiddleware } from './integrations/lobstershell-soul';

const gateway = new Gateway({
  middleware: [
    new SoulMiddleware({
      localThreshold: 0.8,
      cloudThreshold: 0.3,
    }),
  ],
});
```

## 核心能力

### 1. 敏感度分析

```python
score = core.mode_engine.analyzer.analyze('我的密码是 123456')
# → 敏感度 1.0 (高风险)

score = core.mode_engine.analyzer.analyze('今天天气如何？')
# → 敏感度 0.1 (低风险)
```

### 2. 动态模式决策

```python
decision = core.mode_engine.decide('我的密码是 123456')
# → LOCAL_ONLY (强制本地)

decision = core.mode_engine.decide('查询余额')
# → HYBRID (混合模式)

decision = core.mode_engine.decide('今天天气如何？')
# → CLOUD_SANDBOX (可上云)
```

### 3. 零幻觉输出

```python
# AI 输出模板
ai_output = "您的余额为 {{user.balance}}"

# SQL Robot 查询精确数据
# SELECT balance FROM accounts WHERE id = 123

# 精确覆写
final_output = "您的余额为 $15,023.47"  # 精确！
```

## 文件结构

```
lobstershell-soul/
├── soul_architecture/           # 核心组件
│   ├── __init__.py             # 导出接口
│   ├── dynamic_mode_engine.py  # 动态模式引擎 (344 行)
│   ├── layered_security.py     # 分层安全系统 (527 行)
│   ├── zero_hallucination_overwriter.py  # 零幻觉覆写 (478 行)
│   ├── audit_chain.py          # 审计链 (377 行)
│   ├── soul_core.py            # 整合核心 (437 行)
│   ├── example_usage.py        # 使用示例 (290 行)
│   └── test_core.py            # 单元测试 (374 行)
├── SOUL_ARCHITECTURE_SUMMARY.md  # 架构总结
└── README.md                   # 本文件
```

## 测试

```bash
cd integrations/lobstershell-soul
python3 -c "
import sys
sys.path.insert(0, '.')
from soul_architecture import SoulCore
core = SoulCore()
print('✅ 初始化成功')
"
```

## 特性

- ✅ **零依赖**：纯 Python 标准库
- ✅ **支持简/繁/英文**：已测试通过
- ✅ **生产就绪**：所有核心测试通过
- ✅ **易于移植**：2,892 行核心代码
- ✅ **完整文档**：README + 架构文档 + 示例

## 集成状态

- ✅ **Python 版本**：完成，可用
- 🚧 **TypeScript 版本**：开发中
- 🚧 **OpenClaw 中间件**：规划中

## 下一步

1. **立即使用**：复制 `soul_architecture/` 到你的 Python 项目
2. **TypeScript 移植**：将核心逻辑移植到 TypeScript
3. **OpenClaw 集成**：创建 Gateway 中间件
4. **扩展功能**：添加更多敏感度规则、数据源支持

## 来源

基于 MIT 开源项目 [LobsterShell](https://github.com/gk0729/LobsterShell) 抽取核心灵魂架构。

抽取日期：2026-02-18

## 许可证

MIT License
