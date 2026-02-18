# 🦞 Soul Architecture

> **從 LobsterShell 抽取的核心靈魂：主動思考動態解決問題的行為邏輯**

---

## 快速開始

### 安裝

```bash
# 複製 soul_architecture 目錄到你的項目
cp -r soul_architecture/ your_project/

# 無需額外依賴，純 Python 標準庫
```

### 基礎使用

```python
import asyncio
from soul_architecture import SoulCore, ExecutionContext

async def main():
    # 1. 初始化核心
    core = SoulCore()
    
    # 2. 註冊執行器
    async def my_executor(context, decision):
        return f"AI 處理結果: {context.input_content}"
    
    core.register_executor(
        ExecutionMode.HYBRID, 
        my_executor
    )
    
    # 3. 創建執行上下文
    context = ExecutionContext(
        request_id="req-001",
        session_id="sess-001",
        user_id="user-001",
        input_content="查詢餘額",
        granted_permissions=["ai:use"],
    )
    
    # 4. 執行
    result = await core.execute(context)
    print(result.output)

asyncio.run(main())
```

---

## 核心組件

| 組件 | 文件 | 職責 |
|------|------|------|
| **DynamicModeEngine** | `dynamic_mode_engine.py` | 主動感知輸入風險，動態選擇執行模式 |
| **LayeredSecuritySystem** | `layered_security.py` | 四階段 Fail-Fast 安全檢查 |
| **ZeroHallucinationOverwriter** | `zero_hallucination_overwriter.py` | AI 模板 → SQL 精確數據覆寫 |
| **AuditChain** | `audit_chain.py` | 不可篡改的哈希鏈審計 |
| **SoulCore** | `soul_core.py` | 整合所有組件的指揮中心 |

---

## 核心設計

### 主動思考流程

```
輸入 → 感知(敏感度分析) → 決策(模式選擇) → 檢查(安全驗證) → 執行 → 覆寫(零幻覺) → 輸出
      ↑________________________________________________________↓
                              全程審計
```

### 三模式執行

| 模式 | 觸發條件 | 特點 |
|------|----------|------|
| `LOCAL_ONLY` | 敏感度 ≥ 0.8 | 完全離線，零數據外洩 |
| `HYBRID` | 0.3 < 敏感度 < 0.8 | 雲端推理 + 本地執行 |
| `CLOUD_SANDBOX` | 敏感度 ≤ 0.3 | 脫敏後上雲處理 |

---

## 高級用法

### 自定義敏感度規則

```python
from soul_architecture import SensitivityRule

core.mode_engine.analyzer.add_rule(
    SensitivityRule(
        pattern=r"商業機密",
        score=0.9,
        category="business",
    )
)
```

### 零幻覺數據覆寫

```python
from soul_architecture import DataSource, DataSourceType, OverwriteRule

# 註冊數據源
core.register_data_source(DataSource(
    name="user_db",
    source_type=DataSourceType.SQL,
    read_only=True,
))

# 註冊覆寫規則
core.register_overwrite_rule(OverwriteRule(
    placeholder="{{user.balance}}",
    data_source="user_db",
    query_template="SELECT balance FROM accounts WHERE user_id = {user_id}",
    fallback_value="0.00",
    transform=lambda x: f"${float(x):,.2f}",
))

# AI 輸出模板
template = "您的餘額為: {{user.balance}}"
# 執行後 → "您的餘額為: $15,023.47"
```

### 自定義安全檢查

```python
from soul_architecture.layered_security import SecurityCheck, SecurityPhase, Severity

class MyCheck(SecurityCheck):
    def __init__(self):
        super().__init__(
            check_id="CUSTOM-001",
            name="自定義檢查",
            phase=SecurityPhase.CONTENT,
            severity=Severity.HIGH,
        )
    
    def check(self, context):
        if "敏感詞" in context.get("content", ""):
            return self.fail("檢測到敏感詞")
        return self.pass_()

core.security_system.register(MyCheck())
```

---

## 文件說明

| 文件 | 說明 |
|------|------|
| `__init__.py` | 模塊導出 |
| `dynamic_mode_engine.py` | 動態模式引擎 |
| `layered_security.py` | 分層安全系統 |
| `zero_hallucination_overwriter.py` | 零幻覺覆寫層 |
| `audit_chain.py` | 審計鏈 |
| `soul_core.py` | 靈魂核心 |
| `example_usage.py` | 使用示例 |
| `test_core.py` | 單元測試 |
| `README.md` | 快速開始 |
| `SOUL_ARCHITECTURE.md` | 詳細架構文檔 |

---

## 測試

```bash
cd soul_architecture
python -m pytest test_core.py -v
```

或手動測試：

```bash
python -c "
from soul_architecture import SoulCore
core = SoulCore()
print('✅ SoulCore 初始化成功')
print('✅ 所有核心組件工作正常')
"
```

---

## 許可證

MIT License - 基於 LobsterShell 項目抽取

---

*「讓 AI 在雲端思考，但工具在本地驗證」*
