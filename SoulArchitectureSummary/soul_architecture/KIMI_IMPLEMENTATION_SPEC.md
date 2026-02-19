# LobsterSoul 實作規格（可直接交給 Kimi Code K2.5）

## 1) 目標
建立一個「目標導向、可逆向拆解、可動態重規劃」的執行核心：

- 輸入一個最終目標
- 逆向推導必要條件
- 生成可執行的小任務鏈
- 根據外部信號動態調整任務鏈
- 直到目標達成

---

## 2) 核心資料模型

```python
@dataclass
class Goal:
    goal_id: str
    title: str
    success_metric: str
    target_value: float | str
    deadline: str | None

@dataclass
class Condition:
    condition_id: str
    goal_id: str
    statement: str
    rationale: str

@dataclass
class Task:
    task_id: str
    condition_id: str
    title: str
    done_definition: str
    priority: int
    status: str  # todo/running/blocked/done
    dependencies: list[str]

@dataclass
class ReplanSignal:
    signal_type: str  # risk_up / task_blocked / resource_change / goal_drift
    payload: dict
    timestamp: str
```

---

## 3) 模組邊界

### A. GoalParser
- 輸入：自然語言目標
- 輸出：`Goal`
- 規則：必須有「成功指標」與「完成定義」

### B. ReversePlanner
- 輸入：`Goal`
- 輸出：`Condition[]`
- 規則：每個 Condition 都要能回答「為什麼是必要條件」

### C. TaskGraphBuilder
- 輸入：`Condition[]`
- 輸出：`Task[]`（DAG）
- 規則：
  - 每個 Task 都可驗收（done_definition）
  - 依賴不可形成循環

### D. AdaptiveReplanner
- 輸入：`Task[] + ReplanSignal`
- 輸出：更新後 `Task[]`
- 規則：
  - 若 `risk_up`：提高安全等級/切本地模式
  - 若 `task_blocked`：自動找替代任務或調整依賴
  - 若 `goal_drift`：重新生成 Condition 並局部重建 DAG

### E. ProgressEvaluator
- 輸入：`Goal + Task[] + 執行結果`
- 輸出：`goal_progress`（0~1）與 `is_goal_achieved`

---

## 4) 執行流程（狀態機）

1. `INIT`: 解析目標
2. `DECOMPOSE`: 逆向拆解必要條件
3. `PLAN`: 生成任務 DAG
4. `EXECUTE`: 執行可執行任務
5. `EVALUATE`: 估算目標進度
6. `REPLAN`（可重入）: 根據信號調整任務鏈
7. `DONE`: 達成成功指標

---

## 5) 與現有 Soul 架構整合

- 模式決策：交給 `DynamicModeEngine`
- 安全檢查：交給 `LayeredSecuritySystem`
- 精確數據輸出：交給 `ZeroHallucinationOverwriter`
- 全程留痕：交給 `AuditChain`

建議新增一層：

- `GoalDrivenOrchestrator`（只管目標與任務鏈）
- 再調用 `SoulCore.execute()` 做單步任務執行

---

## 6) MVP 驗收標準

- 可從 1 個目標自動產生 ≥ 5 個任務
- 任務依賴正確（DAG 無循環）
- 可處理至少 3 種重規劃信號
- 任務狀態可追蹤、可回放
- 審計鏈可驗證完整性

---

## 7) 測試案例（最少）

1. 正常流程：目標 → 任務 → 完成
2. 任務阻塞：觸發替代任務並繼續
3. 風險升高：模式切到 `LOCAL_ONLY`
4. 目標漂移：重建部分任務鏈
5. 審計驗證：任務鏈修改前後可追蹤

---

## 8) 非功能要求

- 可觀測性：每步均輸出可讀日誌
- 決策可解釋：每次重規劃需附 `reason`
- 可恢復：中斷後可從最近一次狀態恢復
- 可配置：閾值、優先級策略、最大重規劃次數可調

---

## 9) Kimi 執行指令模板

請 Kimi 依序完成：

1. 建立 `goal_orchestrator.py` 與資料模型
2. 實作 `reverse_decompose(goal)`
3. 實作 `build_task_graph(conditions)`
4. 實作 `replan(tasks, signal)`
5. 串接 `SoulCore` 單步執行
6. 補齊 `pytest` 測試
7. 更新 README 的 API 用例

完成後輸出：

- 架構圖
- 關鍵類別說明
- 可直接執行示例
- 測試結果
