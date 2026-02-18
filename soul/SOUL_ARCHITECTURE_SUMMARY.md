# 🦞 LobsterShell 靈魂架構抽取總結

## 項目概述

成功從 https://github.com/gk0729/LobsterShell 項目抽取核心「靈魂」——**主動思考動態解決問題的行為邏輯**，並優化為可移植的精煉架構。

---

## 抽取的核心邏輯

### 1. 主動感知系統 (Dynamic Mode Engine)

**原項目**: `00_core/mode_controller.py` + `00_core/policy_engine.py`

**抽取精華**:
- 敏感度分析器：主動掃描輸入內容的風險級別
- 三模式決策：Local-Only / Hybrid / Cloud-Sandbox
- 動態路由：根據風險自動選擇執行路徑

```python
# 核心邏輯
if sensitivity >= 0.8:     → LOCAL_ONLY (高風險，完全本地)
elif sensitivity <= 0.3:   → CLOUD_SANDBOX (低風險，可上雲)
else:                      → HYBRID (中風險，混合模式)
```

### 2. 分層安全檢查 (Layered Security)

**原項目**: `core/security/secureclaw_checker.py`

**抽取精華**:
- 四階段檢查：入口 → 內容 → 行為 → 執行
- Fail-Fast 機制：關鍵問題立即阻止
- 55+ 安全檢查項的精煉核心

```
Phase 1 (入口): 身份驗證、授權、租戶隔離
Phase 2 (內容): Prompt 注入、PII 檢測、憑證洩漏
Phase 3 (行為): 工具白名單、危險操作檢測
Phase 4 (執行): SQL 只讀、SQL 注入、參數校驗
```

### 3. 零幻覺數據覆寫 (Zero Hallucination Overwriter)

**原項目**: `docs/AI_Zero_Hallucination_Principle.md` + `tools/lobster-tool-sql/`

**抽取精華**:
- **核心原理**: AI 只輸出模板，精確數據由 SQL Robot 覆寫
- **物理隔離**: AI 無法接觸真實數據源
- **三能力原則**: 核對 / 複製 / 粘貼（無創造）

```
AI 輸出（含佔位符）:  "您的餘額為: {{user.balance}}"
                            ↓
SQL Robot 查詢:        SELECT balance FROM accounts WHERE id = 123
                            ↓
數據覆寫:              "您的餘額為: $15,023.47" (精確數據)
```

### 4. 不可篡改審計鏈 (Audit Chain)

**原項目**: `00_core/audit_logger.py`

**抽取精華**:
- 哈希鏈結構：Entry N 的 hash 依賴 Entry N-1
- WORM (Write Once Read Many) 存儲
- 完整性驗證：任何篡改都會被檢測

```
Entry 1: data + hash_1
Entry 2: data + prev_hash=hash_1 + hash_2
Entry 3: data + prev_hash=hash_2 + hash_3
...
```

---

## 架構對比

| 特性 | 原 LobsterShell | Soul Architecture |
|------|-----------------|-------------------|
| **體積** | 完整項目 (~50MB) | 核心靈魂 (~30KB) |
| **依賴** | 多個外部依賴 | 純 Python 標準庫 |
| **功能** | 完整微內核 + 工具生態 | 核心行為邏輯 |
| **用途** | 生產部署 | 移植整合 |
| **擴展性** | 需要遵循完整接口 | 精簡易於擴展 |

---

## 文件結構

```
soul_architecture/
├── __init__.py                    # 導出所有組件
├── dynamic_mode_engine.py         # 377 lines - 動態模式引擎
├── layered_security.py            # 527 lines - 分層安全系統
├── zero_hallucination_overwriter.py  # 478 lines - 零幻覺覆寫
├── audit_chain.py                 # 377 lines - 審計鏈
├── soul_core.py                   # 437 lines - 整合核心
├── example_usage.py               # 290 lines - 使用示例
├── test_core.py                   # 374 lines - 單元測試
├── README.md                      # 快速開始
└── SOUL_ARCHITECTURE.md           # 詳細文檔

Total: ~2,900 lines of pure Python
```

---

## 核心價值

### 1. 主動感知而非被動響應

```python
# 傳統: 發生問題後處理
try:
    result = ai.process(input)
except SecurityError:
    handle_error()

# Soul: 執行前主動分析風險
decision = engine.decide(input)
if decision.mode == ExecutionMode.LOCAL_ONLY:
    # 高風險內容自動隔離
    process_locally(input)
```

### 2. 動態適應而非固定配置

```python
# 同一系統，根據輸入動態調整
"今天天氣如何？"     → CLOUD (敏感度 0.1)
"查詢客戶資料"       → HYBRID (敏感度 0.5)
"我的密碼是 123456" → LOCAL (敏感度 0.95)
```

### 3. 零幻覺輸出

```
傳統 AI:
  Q: "我的餘額多少？"
  A: "您的餘額約為 $15,000" (可能錯誤)

LobsterShell:
  Q: "我的餘額多少？"
  A: "您的餘額為 {{user.balance}}" (模板)
     ↓ SQL Robot 覆寫
  A: "您的餘額為 $15,023.47" (精確)
```

### 4. 全程可審計

```python
# 每個決策和執行都記錄
audit.create_entry(
    event_type=AuditEventType.MODE_DECISION,
    decision="local_only",
    reason="敏感度 0.95 超過閾值 0.8",
    confidence=0.95,
)
# 哈希鏈確保不可篡改
```

---

## 移植使用

### 步驟 1: 複製文件

```bash
cp -r soul_architecture/ your_project/
```

### 步驟 2: 整合到現有項目

```python
from soul_architecture import SoulCore, ExecutionContext

class YourAIAgent:
    def __init__(self):
        self.soul = SoulCore(
            local_threshold=0.8,
            cloud_threshold=0.3,
        )
        
        # 註冊你的執行器
        self.soul.register_executor(
            ExecutionMode.HYBRID, 
            self._execute_hybrid
        )
    
    async def process(self, user_input: str):
        context = ExecutionContext(
            request_id=generate_id(),
            input_content=user_input,
        )
        
        result = await self.soul.execute(context)
        return result.output
```

### 步驟 3: 自定義擴展

```python
# 添加自定義敏感度規則
soul.mode_engine.analyzer.add_rule(
    SensitivityRule(
        pattern=r"你的自定義模式",
        score=0.9,
        category="custom",
    )
)

# 添加自定義安全檢查
soul.security_system.register(MyCustomCheck())

# 註冊數據源
soul.register_data_source(DataSource(...))

# 註冊覆寫規則
soul.register_overwrite_rule(OverwriteRule(...))
```

---

## 測試驗證

```bash
$ python -c "
from soul_architecture import SoulCore
core = SoulCore()
print('✅ 初始化成功')

# 測試敏感度分析
result = core.mode_engine.analyzer.analyze('我的密碼是 123')
print(f'✅ 敏感度分析: {result[\"score\"]:.2f}')

# 測試模式決策
d = core.mode_engine.decide('我的信用卡號是 4111...')
print(f'✅ 模式決策: {d.mode.value}')

# 測試安全檢查
r = core.security_system.run_all({
    'user_id': 'test',
    'auth_token': 'test',
    'content': '查詢',
    'tool_whitelist': ['read_query'],
    'tool_name': 'read_query',
})
print(f'✅ 安全檢查: {r.risk_level}')

print('✅ 所有核心組件工作正常!')
"

✅ 初始化成功
✅ 敏感度分析: 0.95
✅ 模式決策: local_only
✅ 安全檢查: low
✅ 所有核心組件工作正常!
```

---

## 總結

這個抽取的 **Soul Architecture** 包含了 LobsterShell 最核心的「主動思考動態解決問題」的行為邏輯：

1. **主動感知**: 自動分析輸入風險級別
2. **動態決策**: 根據風險選擇最適執行模式
3. **分層防護**: 多階段安全檢查，Fail-Fast
4. **零幻覺**: AI 模板 + SQL 精確數據覆寫
5. **可審計**: 完整的執行記錄和完整性驗證

這是一個精煉、無依賴、易於移植的核心架構，可以作為任何 AI 系統的「安全靈魂」層。

---

*基於 MIT 開源項目 LobsterShell 抽取和重構*
*抽取日期: 2026-02-18*
