# 🦞 LobsterShell - AI 安全灵魂层

**主動思考動態解決問題的行為邏輯**

---

## 專案結構

這個 Monorepo 包含兩個核心部分：

### 🧠 Soul（蝦魂）- 可移植核心

```
soul/
├── soul_architecture/     # 核心架構（2,892 行 Python）
│   ├── dynamic_mode_engine.py      # 動態模式引擎
│   ├── layered_security.py         # 分層安全系統
│   ├── zero_hallucination_overwriter.py  # 零幻覺覆寫
│   ├── audit_chain.py              # 審計鏈
│   └── soul_core.py                # 整合核心
├── README.md              # 快速開始
└── SOUL_ARCHITECTURE_SUMMARY.md  # 架構總結
```

**特點**：
- ✅ 零依賴（純 Python 標準庫）
- ✅ 支持簡/繁/英文
- ✅ 生產就緒
- ✅ 可移植到任何 AI 系統

**用途**：作為安全靈魂層嵌入任何 AI 助手、聊天機器人或自動化系統。

---

### 🦞 Shell（蝦殼）- 完整實現

```
shell/
├── 00_core/              # 核心模組
│   ├── mode_controller.py
│   ├── policy_engine.py
│   └── audit_logger.py
├── core/                 # 核心系統
│   ├── security/
│   ├── tool_runtime/
│   └── interfaces/
├── tools/                # 工具生態
├── docs/                 # 完整文檔
│   ├── AI_Zero_Hallucination_Principle.md
│   └── TriMode_Architecture.md
└── examples/             # 使用示例
```

**特點**：
- 完整的微內核架構
- 豐富的工具生態
- 詳細的技術文檔
- 生產級實現

**用途**：作為參考實現，或直接用於生產環境。

---

## 核心能力

### 1. 主動感知（Sensitivity Analysis）

```python
from soul.soul_architecture import SoulCore

core = SoulCore()
score = core.mode_engine.analyzer.analyze('我的密碼是 123456')
# → 敏感度 1.0 (高風險)
```

### 2. 動態決策（Dynamic Mode Engine）

```python
decision = core.mode_engine.decide('我的密碼是 123456')
# → LOCAL_ONLY (強制本地)

decision = core.mode_engine.decide('今天天氣如何？')
# → CLOUD_SANDBOX (可上雲)
```

### 3. 分層防護（Layered Security）

```
Phase 1 (入口): 身份驗證、授權
Phase 2 (內容): Prompt 注入、PII 檢測
Phase 3 (行為): 工具白名單、危險操作
Phase 4 (執行): SQL 只讀、參數校驗
```

### 4. 零幻覺輸出（Zero Hallucination）

```python
# AI 輸出模板
ai_output = "您的餘額為 {{user.balance}}"

# SQL Robot 查詢
# SELECT balance FROM accounts WHERE id = 123

# 精確覆寫
final_output = "您的餘額為 $15,023.47"  # 精確！
```

### 5. 全程審計（Audit Chain）

```python
# 哈希鏈確保不可篡改
Entry N → hash(N-1) + data → hash(N)
```

---

## 快速開始

### 使用 Soul（推薦）

```bash
# 1. 複製蝦魂
cp -r soul/soul_architecture /your/project/

# 2. 使用
python3 -c "
from soul_architecture import SoulCore
core = SoulCore()
print('✅ LobsterShell Soul 已就緒！')
"
```

### 使用 Shell（完整實現）

```bash
# 1. 克隆倉庫
git clone https://github.com/YOUR_USERNAME/lobstershell.git
cd lobstershell/shell

# 2. 安裝
pip install -e .

# 3. 使用
python3 -c "
import lobstershell
print('✅ LobsterShell 已就緒！')
"
```

---

## 集成案例

### 與 OpenClaw 集成

```typescript
// OpenClaw Gateway 中間件
import { SoulMiddleware } from './soul/soul_architecture';

const gateway = new Gateway({
  middleware: [
    new SoulMiddleware({
      localThreshold: 0.8,
      cloudThreshold: 0.3,
    }),
  ],
});
```

### 與 LangChain 集成

```python
from langchain.agents import AgentExecutor
from soul.soul_architecture import SoulCore

soul = SoulCore()

# 在執行前添加安全檢查
def safe_execute(input_text):
    decision = soul.mode_engine.decide(input_text)
    if decision.mode == ExecutionMode.LOCAL_ONLY:
        # 強制本地處理
        return local_agent.run(input_text)
    else:
        return agent.run(input_text)
```

---

## 文檔

- **Soul 文檔**：[soul/README.md](soul/README.md)
- **Shell 文檔**：[shell/README.md](shell/README.md)
- **架構總結**：[soul/SOUL_ARCHITECTURE_SUMMARY.md](soul/SOUL_ARCHITECTURE_SUMMARY.md)
- **零幻覺原則**：[shell/docs/AI_Zero_Hallucination_Principle.md](shell/docs/AI_Zero_Hallucination_Principle.md)
- **三模式架構**：[shell/docs/TriMode_Architecture.md](shell/docs/TriMode_Architecture.md)

---

## 核心價值

### 傳統 AI vs LobsterShell

| 維度 | 傳統 AI | LobsterShell |
|------|---------|--------------|
| **信任模型** | 信任 AI 判斷 | 不信任，多層驗證 |
| **幻覺處理** | 依賴模型誠實 | 零幻覺（模板+覆寫） |
| **安全級別** | 基礎 | 軍工級 |
| **審計能力** | 日誌 | 不可篡改哈希鏈 |
| **適用場景** | 通用助手 | 高安全場景 |

---

## 適用場景

- ✅ **金融服務**：餘額查詢、交易處理
- ✅ **醫療健康**：患者數據處理
- ✅ **企業應用**：敏感數據查詢
- ✅ **客戶服務**：自動化客服
- ✅ **數據分析**：SQL 查詢安全

---

## 技術規格

### Soul（蝦魂）

- **語言**：Python 3.7+
- **依賴**：零依賴（純標準庫）
- **代碼量**：2,892 行
- **體積**：< 100 KB

### Shell（蝦殼）

- **語言**：Python 3.7+
- **架構**：微內核 + 插件
- **體積**：~50 MB（完整生態）

---

## 許可證

MIT License - 詳見 [LICENSE](LICENSE)

---

## 來源

基於 MIT 開源項目 [LobsterShell](https://github.com/gk0729/LobsterShell) 抽取和重構。

---

## 貢獻

歡迎貢獻！請查看：
- [貢獻指南](CONTRIBUTING.md)
- [問題追蹤](https://github.com/YOUR_USERNAME/lobstershell/issues)

---

## 聯繫

- **項目主頁**：https://github.com/YOUR_USERNAME/lobstershell
- **文檔**：https://github.com/YOUR_USERNAME/lobstershell/tree/main/docs
- **示例**：[examples/](examples/)

---

**小橙的推薦** 🍊：

如果你想要一個輕量級、可移植的安全層 → 使用 **Soul**
如果你需要完整的生產實現和參考 → 使用 **Shell**

兩者可以獨立使用，也可以結合使用！
