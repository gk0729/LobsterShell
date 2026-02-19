# 🦞 LobsterShell Soul Architecture

**從 LobsterShell 抽取的「主動思考動態解決問題」核心邏輯**

---

## 📖 專案起源

**原始項目**：[LobsterShell](https://github.com/gk0729/LobsterShell)（MIT 開源）

**抽取目標**：主動思考、動態解決問題的行為邏輯

**抽取方法**：使用 KimiCode 分析源碼，識別核心架構，優化重構

**抽取日期**：2026-02-18

---

## 🎯 專案定位

這不是 LobsterShell 的 Fork，而是從中抽取的**精煉靈魂層**，可以：

- ✅ 作為獨立的安全層使用
- ✅ 移植到任何 AI 系統
- ✅ 嵌入 OpenClaw、LangChain 等框架
- ✅ 作為 LobsterShell 的輕量級核心

---

## 📂 專案結構

```
lobstershell/
├── soul/                      # 🧠 蝦魂（抽取的核心邏輯）
│   ├── soul_architecture/     # 核心架構（2,892 行 Python）
│   │   ├── dynamic_mode_engine.py          # 動態模式引擎 (344 行)
│   │   ├── layered_security.py             # 分層安全系統 (527 行)
│   │   ├── zero_hallucination_overwriter.py # 零幻覺覆寫 (478 行)
│   │   ├── audit_chain.py                  # 審計鏈 (377 行)
│   │   ├── soul_core.py                    # 整合核心 (437 行)
│   │   ├── example_usage.py                # 使用示例 (290 行)
│   │   └── test_core.py                    # 單元測試 (374 行)
│   ├── README.md                          # Soul 快速開始
│   └── SOUL_ARCHITECTURE_SUMMARY.md       # 架構總結
│
├── shell/                     # 🦞 蝦殼（完整參考實現）
│   ├── 00_core/               # 核心模組
│   ├── core/                  # 核心系統
│   ├── tools/                 # 工具生態
│   ├── docs/                  # 技術文檔
│   │   ├── AI_Zero_Hallucination_Principle.md
│   │   ├── TriMode_Architecture.md
│   │   └── SecureClaw_Integration.md
│   └── examples/              # 使用示例
│
├── examples/                  # 📚 集成案例
│   └── README.md              # OpenClaw、LangChain 示例
│
├── README.md                  # 本文件
├── CONTRIBUTING.md            # 貢獻指南
├── LICENSE                    # MIT 許可證
└── .gitignore                 # Git 忽略規則
```

---

## 🧠 核心能力（從 LobsterShell 抽取）

### 1. 主動感知（Sensitivity Analysis）

**傳統做法**：被動響應，問題發生後處理
**LobsterShell**：主動分析風險，執行前預判

```python
from soul.soul_architecture import SoulCore

core = SoulCore()

# 自動分析輸入風險級別 (0-1)
score = core.mode_engine.analyzer.analyze('我的密碼是 123456')
# → 敏感度 1.0 (極高風險)

score = core.mode_engine.analyzer.analyze('今天天氣如何？')
# → 敏感度 0.1 (低風險)
```

**支持語言**：簡體中文、繁體中文、英文

---

### 2. 動態決策（Tri-Mode Engine）

**傳統做法**：固定配置，所有請求相同處理
**LobsterShell**：根據風險動態選擇執行路徑

```python
# 三模式自動切換
decision = core.mode_engine.decide('我的密碼是 123456')
# → LOCAL_ONLY (敏感度 ≥0.8，強制本地)

decision = core.mode_engine.decide('查詢餘額')
# → HYBRID (敏感度 0.3-0.8，混合模式)

decision = core.mode_engine.decide('今天天氣如何？')
# → CLOUD_SANDBOX (敏感度 ≤0.3，可上雲)
```

**決策邏輯**：
```
敏感度 ≥ 0.8  → LOCAL_ONLY (完全本地，零外洩)
敏感度 0.3-0.8 → HYBRID (雲端思考 + 本地執行)
敏感度 ≤ 0.3  → CLOUD_SANDBOX (輕量脫敏後上雲)
```

---

### 3. 分層防護（Layered Security）

**傳統做法**：單層權限控制
**LobsterShell**：四階段 Fail-Fast 防護

```
Phase 1 (入口): 身份驗證、授權、租戶隔離
Phase 2 (內容): Prompt 注入、PII 檢測、憑證洩漏
Phase 3 (行為): 工具白名單、危險操作檢測
Phase 4 (執行): SQL 只讀、SQL 注入、參數校驗
```

**Fail-Fast 機制**：關鍵問題立即阻止，不進入下一階段

---

### 4. 零幻覺輸出（Zero Hallucination）

**傳統做法**：AI 直接輸出數據，可能幻覺
**LobsterShell**：AI 只輸出模板，精確數據由系統覆寫

```python
# 傳統 AI（可能錯誤）
AI: "您的餘額約為 $15,000"  ⚠️ 幻覺

# LobsterShell（精確）
AI 模板:     "您的餘額為 {{user.balance}}"
                  ↓
SQL Robot:   SELECT balance FROM accounts WHERE id = 123
                  ↓
精確覆寫:    "您的餘額為 $15,023.47"  ✅ 精確！
```

**核心原理**：AI 只做「核對 / 複製 / 粘貼」，無創造能力

---

### 5. 全程審計（Audit Chain）

**傳統做法**：普通日誌，可被篡改
**LobsterShell**：哈希鏈確保不可篡改

```python
# 哈希鏈結構
Entry 1: data + hash_1
Entry 2: data + prev_hash=hash_1 + hash_2
Entry 3: data + prev_hash=hash_2 + hash_3
...

# 任何篡改都會被檢測
```

**特性**：WORM (Write Once Read Many) 存儲

---

## 🚀 快速開始

### 方法 1：使用 Soul（推薦）

```bash
# 1. 複製核心到你的項目
cp -r soul/soul_architecture /your/project/

# 2. 直接使用（零依賴）
python3 -c "
from soul_architecture import SoulCore

core = SoulCore()

# 敏感度分析
score = core.mode_engine.analyzer.analyze('我的密碼')
print(f'敏感度: {score[\"score\"]:.2f}')

# 模式決策
decision = core.mode_engine.decide('查詢餘額')
print(f'模式: {decision.mode.value}')

print('✅ LobsterShell Soul 已就緒！')
"
```

**輸出**：
```
敏感度: 1.00
模式: local_only
✅ LobsterShell Soul 已就緒！
```

---

### 方法 2：使用 Shell（完整實現）

```bash
# 1. 克隆倉庫
git clone https://github.com/gk0729/lobstershell.git
cd lobstershell/shell

# 2. 安裝（可選）
pip install -e .

# 3. 使用
python3 -c "
import lobstershell
print('✅ LobsterShell 完整版已就緒！')
"
```

---

### 方法 3：與 OpenClaw 控制頁相容（`127.0.0.1:18789`）

LobsterShell 現在提供 OpenClaw Web 相容 Gateway（HTTP + WebSocket 透明代理）。

```bash
# 啟動相容層（預設 listen: 127.0.0.1:18790，轉發到 OpenClaw: 127.0.0.1:18789）
python -m cli.lobster_cli gateway compat
```

一鍵同時啟動（上游 OpenClaw + 相容層）：

```bash
./scripts/one_click_openclaw_compat.sh
```

一鍵停止（關閉 18789/18791）：

```bash
./scripts/stop_openclaw_compat.sh
```

若你要「維持控制頁仍是 127.0.0.1:18789」：

1. 先把 OpenClaw 改跑到 `127.0.0.1:18791`（或任一空閒埠）
2. 再讓 LobsterShell 相容層監聽 `18789`：

```bash
python -m cli.lobster_cli gateway compat \
    --listen-host 127.0.0.1 \
    --listen-port 18789 \
    --target-url http://127.0.0.1:18791
```

這樣你原本的 OpenClaw 網頁入口不需改網址，仍可直接使用。

---

## 📊 與原始 LobsterShell 的區別

| 維度 | 原始 LobsterShell | Soul Architecture |
|------|-------------------|-------------------|
| **體積** | ~50 MB (完整生態) | < 100 KB (核心代碼) |
| **依賴** | 多個外部依賴 | 零依賴（純標準庫） |
| **用途** | 生產部署 | 可移植核心 |
| **集成難度** | 需要完整架構 | 複製即用 |
| **維護成本** | 高 | 低 |

**關係**：
- Soul 是從 Shell 抽取的精華
- Shell 是完整的參考實現
- 兩者可以獨立使用，也可以結合使用

---

## 💡 適用場景

### 推薦使用 Soul（蝦魂）

- ✅ 需要輕量級安全層
- ✅ 移植到現有項目
- ✅ 嵌入 AI 助手/聊天機器人
- ✅ 需要快速原型驗證

### 推薦使用 Shell（蝦殼）

- ✅ 需要完整參考實現
- ✅ 生產環境部署
- ✅ 學習完整架構
- ✅ 需要豐富工具生態

---

## 🎓 核心哲學

### 傳統 AI 的問題

```
信任 AI 判斷
    ↓
依賴模型誠實
    ↓
可能幻覺
    ↓
安全風險
```

### LobsterShell 的解決方案

```
不信任，多層驗證
    ↓
主動感知風險
    ↓
零幻覺（模板+覆寫）
    ↓
全程可審計
    ↓
安全可控
```

**核心原則**：
> AI 只負責「核對 / 複製 / 粘貼」，絕不創造數據

---

## 📚 文檔

- **Soul 快速開始**：[soul/README.md](soul/README.md)
- **架構總結**：[soul/SOUL_ARCHITECTURE_SUMMARY.md](soul/SOUL_ARCHITECTURE_SUMMARY.md)
- **詳細架構**：[soul/soul_architecture/SOUL_ARCHITECTURE.md](soul/soul_architecture/SOUL_ARCHITECTURE.md)
- **Shell 文檔**：[shell/README.md](shell/README.md)
- **零幻覺原則**：[shell/docs/AI_Zero_Hallucination_Principle.md](shell/docs/AI_Zero_Hallucination_Principle.md)
- **集成示例**：[examples/README.md](examples/README.md)

---

## 🧪 測試

```bash
cd soul/soul_architecture
python3 test_core.py
```

**測試覆蓋**：
- ✅ 敏感度分析（簡/繁/英文）
- ✅ 動態模式決策
- ✅ 安全檢查
- ✅ 審計鏈
- ✅ 整合測試

---

## 🤝 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 許可證

MIT License - 詳見 [LICENSE](LICENSE)

---

## 🙏 致謝

- **原始項目**：[LobsterShell](https://github.com/gk0729/LobsterShell) by gk0729
- **抽取工具**：KimiCode
- **優化整合**：小橙 🍊
- **修Bug整合**：GitHub Copilot GPT-5.3-Codex
---

## 📮 聯繫

- **GitHub**：https://github.com/gk0729/lobstershell
- **問題反饋**：[GitHub Issues](https://github.com/gk0729/lobstershell/issues)

---

**小橙的推薦** 🍊：

> 如果你想要一個輕量級、可移植的安全靈魂層 → 使用 **Soul**
> 如果你需要完整的生產實現和參考 → 使用 **Shell**
>
> 兩者可以獨立使用，也可以結合使用！
