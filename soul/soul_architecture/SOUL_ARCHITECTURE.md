# 🦞 LobsterShell Soul Architecture

> **抽取 LobsterShell 核心靈魂：主動思考動態解決問題的行為邏輯**

---

## 核心理念

LobsterShell 的「靈魂」是一套**主動感知、動態決策、分層防護、零幻覺輸出**的 AI 執行架構。

```
傳統 AI 系統:  Input → AI → Output (可能幻覺)
                        ↓
LobsterShell:   Input → 感知 → 決策 → 安全檢查 → 執行 → 覆寫 → Output (精確)
                        ↑___________________________↓
                                    全程審計
```

---

## 架構組件

### 1. DynamicModeEngine (動態模式引擎)

**核心能力**: 主動分析輸入敏感度，動態選擇最適執行模式

```python
from soul_architecture import DynamicModeEngine, ExecutionMode

engine = DynamicModeEngine(
    local_threshold=0.8,   # 高敏感度 → 本地執行
    cloud_threshold=0.3,   # 低敏感度 → 可上雲
)

decision = engine.decide(
    content="我的信用卡號是 4111-1111-1111-1111",
    user_id="user-001",
)

# decision.mode = ExecutionMode.LOCAL_ONLY
# decision.sensitivity_score = 0.95
# decision.requires_confirmation = True
```

**三種執行模式**:

| 模式 | 敏感度 | 特點 | 適用場景 |
|------|--------|------|----------|
| `LOCAL_ONLY` | ≥ 0.8 | 完全離線，零外洩 | 金融/密碼/身份證 |
| `HYBRID` | 0.3-0.8 | 雲端推理+本地執行 | 一般業務處理 |
| `CLOUD_SANDBOX` | ≤ 0.3 | 脫敏後上雲 | 公開資料查詢 |

---

### 2. LayeredSecuritySystem (分層安全系統)

**核心能力**: 四階段 Fail-Fast 安全檢查

```python
from soul_architecture import LayeredSecuritySystem, SecurityPhase

security = LayeredSecuritySystem(fail_fast=True)

report = security.run_all({
    "user_id": "user-001",
    "content": "查詢餘額",
    "sql": "SELECT * FROM users",
    "granted_permissions": ["database:read"],
})

print(report.risk_level)  # low/medium/high/critical
print(security.generate_report_text(report))
```

**四個 Phase**:

1. **Phase 1 - 入口檢查**: 身份驗證、授權、租戶隔離
2. **Phase 2 - 內容檢查**: Prompt 注入、PII 檢測、憑證洩漏
3. **Phase 3 - 行為檢查**: 工具白名單、危險操作檢測
4. **Phase 4 - 執行檢查**: SQL 只讀、SQL 注入、參數校驗

---

### 3. ZeroHallucinationOverwriter (零幻覺覆寫層)

**核心能力**: 將 AI 的「猜測值」覆寫為「精確數據」

```python
from soul_architecture import ZeroHallucinationOverwriter, OverwriteRule, DataSource

overwriter = ZeroHallucinationOverwriter()

# 註冊數據源
overwriter.register_data_source(DataSource(
    name="user_db",
    source_type=DataSourceType.SQL,
    read_only=True,  # 強制只讀
))

# 註冊覆寫規則
overwriter.register_rule(OverwriteRule(
    placeholder="{{user.balance}}",
    data_source="user_db",
    query_template="SELECT balance FROM accounts WHERE user_id = {user_id}",
    fallback_value="0.00",
    transform=lambda x: f"${float(x):,.2f}",
))

# AI 生成模板（含佔位符）
template = "您的餘額為: {{user.balance}}"

# 覆寫
result = await overwriter.overwrite(template, context={"user_id": "123"})
print(result["final_output"])  # "您的餘額為: $15,000.50"
```

**零幻覺原理**:

```
AI 輸出（猜測）:     "您的餘額約為 $15,000"
                           ↓
佔位符模板:           "您的餘額為: {{user.balance}}"
                           ↓
SQL Robot 查詢:       SELECT balance FROM accounts WHERE user_id = 123
                           ↓
精確數據覆寫:         "您的餘額為: $15,023.47"
```

---

### 4. AuditChain (不可篡改審計鏈)

**核心能力**: 所有決策和執行留痕，哈希鏈確保完整性

```python
from soul_architecture import AuditChain, AuditEventType, AuditLevel

audit = AuditChain()

# 記錄審計
audit.create_entry(
    event_type=AuditEventType.MODE_DECISION,
    action="mode_decision",
    description="選擇執行模式",
    session_id="sess-001",
    request_id="req-001",
    decision="local_only",
    confidence=0.95,
)

# 驗證鏈完整性
status = audit.verify_chain()
print(f"審計鏈有效: {status.valid}")
```

---

## 整合使用：SoulCore

`SoulCore` 是所有組件的指揮中心：

```python
from soul_architecture import SoulCore, ExecutionContext

# 1. 初始化
core = SoulCore(
    local_threshold=0.8,
    cloud_threshold=0.3,
    enable_audit=True,
)

# 2. 註冊執行器
async def my_executor(context, decision):
    # 根據決策的模式執行
    return f"AI 輸出: {context.input_content}"

core.register_executor(ExecutionMode.HYBRID, my_executor)

# 3. 配置數據源和覆寫規則
core.register_data_source(...)
core.register_overwrite_rule(...)

# 4. 執行
context = ExecutionContext(
    request_id="req-001",
    session_id="sess-001",
    user_id="user-001",
    input_content="查詢餘額",
)

result = await core.execute(context)
print(result.output)  # 已覆寫的精確輸出
```

---

## 執行流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        執行流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ANALYZE                                                     │
│     ↓ 輸入內容                                                  │
│     ↓ SensitivityAnalyzer 分析敏感度                            │
│     ↓ 輸出: sensitivity_score (0-1)                             │
│                                                                 │
│  2. DECIDE                                                      │
│     ↓ 根據敏感度選擇 ExecutionMode                              │
│     ↓ LOCAL_ONLY / HYBRID / CLOUD_SANDBOX                       │
│     ↓ 輸出: ModeDecision                                        │
│                                                                 │
│  3. SECURITY CHECK                                              │
│     ↓ Phase 1: 入口檢查（身份/授權）                            │
│     ↓ Phase 2: 內容檢查（注入/PII）                             │
│     ↓ Phase 3: 行為檢查（白名單/危險操作）                      │
│     ↓ Phase 4: 執行檢查（SQL只讀/注入）                         │
│     ↓ 輸出: SecurityReport                                      │
│                                                                 │
│  4. EXECUTE                                                     │
│     ↓ 根據 Mode 調用對應 Executor                               │
│     ↓ AI 生成帶佔位符的模板                                     │
│     ↓ 輸出: raw_output (含佔位符)                               │
│                                                                 │
│  5. OVERWRITE                                                   │
│     ↓ ZeroHallucinationOverwriter 解析佔位符                    │
│     ↓ SQL Robot 執行只讀查詢                                    │
│     ↓ 精確數據覆寫佔位符                                        │
│     ↓ 輸出: final_output (精確數據)                             │
│                                                                 │
│  6. AUDIT                                                       │
│     ↓ 記錄所有階段到 AuditChain                                 │
│     ↓ 計算哈希確保完整性                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心優勢

### 1. 主動感知風險

系統主動分析輸入，而非被動等待問題發生：

```python
# 自動檢測到高風險內容
decision = engine.decide("我的密碼是 123456")
# → mode: LOCAL_ONLY
# → requires_confirmation: True
```

### 2. 動態適應場景

根據風險級別動態調整執行策略：

| 場景 | 敏感度 | 模式 | 措施 |
|------|--------|------|------|
| 天氣查詢 | 0.1 | CLOUD | 直接上雲 |
| 文檔總結 | 0.5 | HYBRID | 雲端推理+本地處理 |
| 銀行餘額 | 0.85 | LOCAL | 完全本地執行 |
| 密碼修改 | 0.95 | LOCAL + 確認 | 本地+人工確認 |

### 3. 零幻覺輸出

通過「AI 生成模板 → SQL Robot 覆寫」確保數據精確：

```
❌ 傳統: AI 直接輸出 "您的餘額約為 $15,000" (可能錯誤)
✅ LobsterShell: AI 輸出模板 → SQL 查詢 → "您的餘額為 $15,023.47" (精確)
```

### 4. 完整審計追蹤

所有決策和執行都記錄在不可篡改的審計鏈中：

```
Entry N:   [MODE_DECISION] → hash_N
              ↓ previous_hash = hash_{N-1}
Entry N+1: [SECURITY_CHECK] → hash_{N+1}
              ↓ previous_hash = hash_N
Entry N+2: [DATA_OVERWRITE] → hash_{N+2}
```

---

## 移植指南

### 步驟 1: 複製核心文件

```bash
soul_architecture/
├── __init__.py                    # 導出所有組件
├── dynamic_mode_engine.py         # 動態模式引擎
├── layered_security.py            # 分層安全系統
├── zero_hallucination_overwriter.py  # 零幻覺覆寫層
├── audit_chain.py                 # 審計鏈
├── soul_core.py                   # 靈魂核心（整合）
└── example_usage.py               # 使用示例
```

### 步驟 2: 整合到現有項目

```python
# 在你的項目中
from soul_architecture import SoulCore, ExecutionContext

class YourAIAgent:
    def __init__(self):
        self.soul = SoulCore()
        
        # 註冊你的執行器
        self.soul.register_executor(ExecutionMode.HYBRID, self._execute_hybrid)
    
    async def process(self, user_input: str):
        context = ExecutionContext(
            request_id=generate_id(),
            session_id=self.session_id,
            user_id=self.user_id,
            input_content=user_input,
        )
        
        result = await self.soul.execute(context)
        return result.output
```

### 步驟 3: 自定義擴展

**添加自定義敏感度規則**:

```python
from soul_architecture.dynamic_mode_engine import SensitivityRule

soul.mode_engine.analyzer.add_rule(
    SensitivityRule(
        pattern=r"商業機密|confidential",
        score=0.9,
        category="business",
    )
)
```

**添加自定義安全檢查**:

```python
from soul_architecture.layered_security import SecurityCheck, Severity, SecurityPhase

class MyCustomCheck(SecurityCheck):
    def __init__(self):
        super().__init__(
            check_id="CUSTOM-001",
            name="自定義檢查",
            phase=SecurityPhase.CONTENT,
            severity=Severity.HIGH,
        )
    
    def check(self, context):
        # 你的檢查邏輯
        if "敏感詞" in context.get("content", ""):
            return self.fail("檢測到敏感詞")
        return self.pass_()

soul.security_system.register(MyCustomCheck())
```

---

## 許可證

MIT License - 基於 LobsterShell 項目抽取和重構

---

*「讓 AI 在雲端思考，但工具在本地驗證」*
