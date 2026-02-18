# LobsterShell 示例

這個目錄包含各種集成和使用示例。

---

## 示例列表

### 1. 基本 Soul 使用

```python
# basic_soul_usage.py
from soul.soul_architecture import SoulCore, ExecutionContext

async def main():
    core = SoulCore()

    # 敏感度分析
    score = core.mode_engine.analyzer.analyze('我的密碼是 123456')
    print(f'敏感度: {score["score"]}')

    # 模式決策
    decision = core.mode_engine.decide('查詢餘額')
    print(f'模式: {decision.mode.value}')

    # 執行
    context = ExecutionContext(
        request_id='req-001',
        input_content='查詢餘額',
    )
    result = await core.execute(context)
    print(f'結果: {result.output}')
```

### 2. OpenClaw 集成

```typescript
// openclaw_integration.ts
import { SoulMiddleware } from '../soul/soul_architecture';
import { Gateway } from '@openclaw/gateway';

const gateway = new Gateway({
  middleware: [
    new SoulMiddleware({
      localThreshold: 0.8,
      cloudThreshold: 0.3,
      enableAudit: true,
    }),
  ],
});

gateway.start();
```

### 3. LangChain 集成

```python
# langchain_integration.py
from langchain.agents import AgentExecutor
from langchain.llms import OpenAI
from soul.soul_architecture import SoulCore

class SafeAgentExecutor:
    def __init__(self, agent_executor: AgentExecutor):
        self.agent = agent_executor
        self.soul = SoulCore()

    def run(self, input_text: str):
        # 前置檢查
        decision = self.soul.mode_engine.decide(input_text)

        if decision.mode == ExecutionMode.LOCAL_ONLY:
            # 強制本地處理
            return self._local_run(input_text)
        elif decision.mode == ExecutionMode.HYBRID:
            # 混合模式
            return self._hybrid_run(input_text)
        else:
            # 雲端沙盒
            return self.agent.run(input_text)

    def _local_run(self, input_text):
        # 本地安全處理
        pass

    def _hybrid_run(self, input_text):
        # 混合處理
        pass
```

### 4. 金融服務示例

```python
# financial_service_example.py
from soul.soul_architecture import SoulCore, DataSource, OverwriteRule

# 初始化
core = SoulCore()

# 註冊數據源
core.register_data_source(DataSource(
    name='bank_db',
    connection_string='postgresql://...',
    read_only=True,
))

# 註冊覆寫規則
core.register_overwrite_rule(OverwriteRule(
    pattern=r'\{\{user\.balance\}\}',
    data_source='bank_db',
    query='SELECT balance FROM accounts WHERE user_id = :user_id',
))

# 使用
async def get_balance(user_id: str):
    context = ExecutionContext(
        request_id=f'balance-{user_id}',
        input_content='查詢餘額',
        metadata={'user_id': user_id},
    )

    result = await core.execute(context)
    # AI 輸出: "您的餘額為 {{user.balance}}"
    # 覆寫後: "您的餘額為 $15,023.47"
    return result.output
```

---

## 運行示例

### Python 示例

```bash
cd examples
python3 basic_soul_usage.py
```

### TypeScript 示例

```bash
cd examples
npm install
npm run openclaw_integration
```

---

## 貢獻示例

歡迎添加更多示例！請確保：
- 包含完整的代碼
- 添加詳細的註釋
- 提供運行說明
- 測試通過

---

## 獲取幫助

如果你在運行示例時遇到問題：
1. 查看文檔：[soul/README.md](../soul/README.md)
2. 查看測試：[soul/soul_architecture/test_core.py](../soul/soul_architecture/test_core.py)
3. 創建 Issue：[GitHub Issues](https://github.com/YOUR_USERNAME/lobstershell/issues)

---

**小橙的提示** 🍊：

從 `basic_soul_usage.py` 開始，這是最簡單的入門示例！
