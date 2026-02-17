# Superautobot724 Tri-Mode 架构

> Local-Only / Hybrid / Cloud-Only Sandbox 三模式工业级架构

## 核心设计目标

- **Tri-Mode 运行模式**：Local-Only / Hybrid / Cloud-Only
- **OpenCode**：全部核心组件可用开源技术栈实现
- **国产模型可落地**：本地与云端均可替换为国产/自建模型
- **Zero-Trust + 防幻觉**：云端只做「思考/翻译」，本地掌握「数据 + 执行权」

## 技术栈

| 模组 | 技术栈 | 说明 |
|------|--------|------|
| API Gateway | FastAPI / Gin | 高效 REST/gRPC 入口 |
| Mode Controller | Python + Redis/PostgreSQL | 储存与切换模式配置 |
| Local LLM | Qwen / GLM / Baichuan / LLaMA | 审核者 + 用户代理 |
| Workflow | LangGraph / Haystack | 任务流与工具调度 |
| Cloud Bridge | LiteLLM / 自建 HTTP Client | 统一 OpenAI / 国产云 API |
| SQL Robot | Golang + PostgreSQL | 只读查询 + 精确覆写 |
| Audit Log | PostgreSQL / ClickHouse | 不可篡改审计流水 |
| IM Bot | Telegram / WhatsApp API | 用户互动入口 |

---

## 完整架构树

```
Superautobot724_TriMode
├─ 00_Mode_Controller (运行模式控制层)
│  ├─ 00.01_Mode_Config_Store
│  │  ├─ 支援三模式：Local_Only / Hybrid_Local+API / Cloud_API_Only
│  │  ├─ 支援按「租户 / 用户 / 任务类型」粒度切换
│  │  └─ 支援热更新（无需重启服务）
│  ├─ 00.02_Mode_Router
│  │  ├─ 根据当前模式决定请求路由
│  │  └─ 支援灰度策略
│  └─ 00.03_Mode_Policy_Engine
│     ├─ 定义各模式下允许的模型类型、数据访问级别、工具使用权限
│     └─ 提供审计用「当时模式配置快照」
│
├─ 01_API_Gateway_Layer (本地网关层 - 唯一对外入口)
│  ├─ 01.01_Unified_Rest_Interface
│  │  ├─ REST/gRPC/WebSocket 统一入口
│  │  ├─ 多租户识别（Tenant ID / API Key / JWT）
│  │  └─ 请求节流与速率限制
│  └─ 01.02_Payload_Sanitizer
│     ├─ 基本格式校验
│     ├─ XSS / SQL 注入 / Prompt Injection 初步过滤
│     ├─ PII 探测
│     └─ 将敏感字段标记为「待脱敏」
│
├─ 02_Local_AI_Layer (本地 AI 大脑 + 审核者 + 用户代理)
│  ├─ 02.01_Local_LLM_Core
│  │  ├─ 专门训练的本地模型（3B–7B）
│  │  └─ 任务：意图理解 / 安全判断 / 工具选择 / 用户偏好建模
│  ├─ 02.02_User_Proxy_Agent
│  │  ├─ 模拟用户语气、偏好、决策风格
│  │  └─ 在 Hybrid 模式中代表用户与 API AI「间接互动」
│  ├─ 02.03_API_AI_Input_Reviewer
│  │  └─ 审核即将发往 API AI 的 Prompt
│  ├─ 02.04_API_AI_Output_Reviewer
│  │  └─ 审核 API AI 回应
│  ├─ 02.05_Auto_Reply_Engine
│  │  └─ 用户超时自动回覆
│  └─ 02.06_Sensitive_Data_Masker
│     └─ 敏感数据 Token 化
│
├─ 03_Cloud_Model_Bridge (云端模型桥接层 - API 沙盒)
│  ├─ 03.01_Prompt_Template_Injector
│  │  ├─ 根据任务类型选择模板
│  │  └─ 强制 System Prompt 禁止生成真实数据
│  ├─ 03.02_API_Circuit_Breaker
│  │  ├─ 设定 Token 上限、超时、重试策略
│  │  └─ 异常时回退到本地 AI
│  └─ 03.03_Response_Structure_Enforcer
│     └─ 验证 API 回应符合预期格式
│
├─ 04_Data_Integrity_Layer (数据完整性层 - SQL 机器人)
│  ├─ 04.01_SQL_Robot_Core
│  │  ├─ A_ReadOnly_Query_Runner (只允许 SELECT)
│  │  ├─ B_Exact_Value_Matcher (Token 转为真实查询条件)
│  │  └─ C_Fact_Overwriter (覆写 API AI 生成的猜测值)
│  └─ 04.02_Physical_Merger
│     └─ 将模板中的 {{PLACEHOLDER}} 替换为真实数据
│
├─ 05_User_Interface_Layer (用户介面层)
│  ├─ 05.01_User_Message_Relay
│  ├─ 05.02_API_AI_Message_Proxy
│  └─ 05.03_Local_AI_AutoReply
│
└─ 06_Infrastructure_Layer (基础设施工层)
   ├─ 06.01_Local_Database
   ├─ 06.02_Immutable_Audit_Log
   └─ 06.03_Secret_Manager
```

---

## 三种模式路由

### 1. Local-Only 纯本地模式

```
User → 01_API_Gateway → 02_Local_AI_Layer → 04_Data_Integrity_Layer → User
```

- 完全离线 / 高敏感数据
- 不启用 03_Cloud_Model_Bridge

### 2. Hybrid 混合模式

```
User ↔ 05_User_Interface_Layer
   → 02_Local_AI_Layer (意图 + 脱敏 + 决策)
   → 03_Cloud_Model_Bridge (API AI 沙盒)
   → 02_Local_AI_Layer (输出审核 + 合并)
   → 04_Data_Integrity_Layer (SQL Robot + 真实数据覆写)
   → User
```

- 本地 AI = 审核者 + 用户代理
- Cloud AI = 只做「逻辑翻译 / 规划」

### 3. Cloud-Only Sandbox 纯 API 模式

```
User → 01_API_Gateway
   → 02.06_Sensitive_Data_Masker（轻量脱敏）
   → 03_Cloud_Model_Bridge（API AI）
   → 04_Data_Integrity_Layer（SQL Robot 覆写）
   → User
```

- 没有本地模型资源
- 仍保留 Token 化 + SQL Robot

---

**来源**: Microsoft Copilot 最后整理生成架构图
