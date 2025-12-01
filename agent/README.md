# Stock Analysis Agent Module

## 1. 模块概述 (Module Overview)

本模块实现了一个基于 **A2A (Agent-to-Agent)** 协议的多 Agent 协作系统，专注于股票市场分析。它采用 "Boardroom"（会议室）架构，由一个接待员（Receptionist）、一位主席（Chairman）、一位评论家（Critic）和多位专家（Specialists）组成。

系统使用 **EventBus** 架构实现解耦的事件流式传输，支持实时进度反馈和多订阅者模式。

## 2. 架构设计 (Architecture)

### 2.1 核心架构 (Boardroom Pattern + EventBus)

系统采用分层协作模式 + 事件驱动架构：

1. **Receptionist**: 入口层。分析用户意图，生成研究简报（Research Brief）。
2. **Chairman**: 决策层。基于研究简报和当前上下文，规划下一步行动，指派具体的专家 Agent。
3. **Specialists**: 执行层。具备特定工具的 Agent，负责执行具体任务（如查股价、搜新闻）。
   - `MacroDataInvestigator`: 宏观经济数据
   - `MarketDataInvestigator`: 市场行情数据
   - `SentimentInvestigator`: 舆情情感分析
   - `WebSearchInvestigator`: 通用网络搜索
4. **Critic**: 总结层。在任务结束前审查所有收集到的证据，生成最终的综合回答。
5. **EventBus**: 事件总线。所有 Agent 通过 EventBus 发布事件，API 层订阅并流式传输到前端。

### 2.2 数据流 (Data Flow with EventBus)

```
┌─────────────┐
│   Frontend  │
└──────▲──────┘
       │ (SSE/NDJSON)
       │
┌──────┴──────────────────────────────────────┐
│  API: /chat/stream                          │
│  - Creates session_id                       │
│  - Subscribes to EventBus                   │
│  - Launches agent pipeline in background    │
│  - Yields events to frontend                │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│  EventBus (core/bus.py)                     │
│  - Session-scoped channels                  │
│  - Async publish/subscribe                  │
└──────▲──────────────────────────────────────┘
       │ (publish events)
       │
┌──────┴──────────────────────────────────────┐
│  Agent Pipeline                             │
│  1. Receptionist → Research Brief           │
│  2. Chairman → Plan & Route                 │
│  3. Specialists → Execute & Report          │
│  4. Critic → Final Synthesis                │
│  (All agents publish events independently)  │
└─────────────────────────────────────────────┘
```

**事件类型**:
- `agent_start`: Agent 开始工作
- `agent_message`: Agent 发送消息
- `agent_status_change`: Agent 状态变化（thinking/speaking）
- `routing`: Chairman 路由到下一个 Agent
- `tool_call`: Agent 调用工具
- `agent_end`: Agent 完成工作
- `error`: 错误信息
- `system_end`: 整个工作流完成

### 2.3 A2A 协议集成

每个 Agent 都被封装为独立的 A2A 服务，支持：
- **Agent Card**: 标准化的元数据描述（能力、输入输出 Schema）
- **Task Execution**: 标准化的任务执行接口
- **EventBus Integration**: 所有 Agent 通过 EventBus 发布执行进度

## 3. 目录结构 (Directory Structure)

```
agent/
├── main.py                 # 程序入口，FastAPI 应用定义
├── api/                    # API 接口层
│   ├── routes.py           # REST API (/api/chat, /api/chat/stream)
│   ├── a2a.py              # A2A 协议实现 (/a2a/...)
│   └── models.py           # Pydantic 数据模型
├── core/                   # 核心逻辑层
│   ├── agent.py            # StockAnalysisAgent 主类
│   ├── bus.py              # EventBus 事件总线 ⭐ NEW
│   ├── a2a_client.py       # A2A 客户端，管理 Agent 实例
│   ├── config.py           # 配置管理
│   ├── memory.py           # 对话记忆管理
│   ├── state.py            # AgentState 状态定义
│   ├── prompts.py          # Agent 系统提示词
│   └── agents/             # 各个 Agent 的具体实现
│       ├── a2a_base.py     # A2A Agent 基类
│       ├── utils.py        # Agent 工具函数
│       ├── receptionist.py # 接待员
│       ├── chairman.py     # 主席
│       ├── critic.py       # 评论家
│       ├── macro.py        # 宏观数据专家
│       ├── market.py       # 市场数据专家
│       ├── sentiment.py    # 情感分析专家
│       └── web_search.py   # 网络搜索专家
├── skills/                 # 工具/技能实现 (外部引用)
└── utils/                  # 通用工具函数
```

## 4. 功能特性 (Features)

- **多 Agent 协作**: 动态规划任务路径，非线性执行
- **EventBus 架构**: 解耦的事件流式传输，支持多订阅者
- **A2A 互操作性**: 支持 Google A2A 标准，可被其他 Agent 系统发现和调用
- **ReAct 模式**: 专家 Agent 具备推理-行动能力，并记录详细执行日志
- **实时流式输出**: 通过 EventBus 实时推送 Agent 执行进度到前端

## 5. 使用说明 (Usage)

### 5.1 启动服务

```bash
# 确保配置文件存在
cp agent/config.yaml.example agent/config.yaml
# 编辑 config.yaml，填入 API Key

# 启动服务
python agent/main.py
```

服务默认运行在 `http://0.0.0.0:8001`。

### 5.2 API 调用

#### 标准对话（非流式）
- **Endpoint**: `POST /api/chat`
- **Body**: 
  ```json
  {
    "message": "分析一下 NVDA 的股价和近期新闻",
    "session_id": "optional_session_id"
  }
  ```
- **Response**: 
  ```json
  {
    "response": "...",
    "session_id": "...",
    "tool_calls": [...],
    "success": true
  }
  ```

#### 流式对话（推荐）⭐
- **Endpoint**: `POST /api/chat/stream`
- **Body**: 
  ```json
  {
    "message": "分析一下 NVDA 的股价和近期新闻"
  }
  ```
- **Response**: NDJSON 事件流
  ```json
  {"type":"agent_start","agent":"Receptionist","content":"Analyzing user intent...","timestamp":1234567890.123}
  {"type":"agent_message","agent":"Receptionist","content":"分析 NVDA 股价...","timestamp":1234567890.456}
  {"type":"routing","from":"Chairman","to":"MarketDataInvestigator","instruction":"获取 NVDA 当前股价"}
  {"type":"tool_call","agent":"MarketDataInvestigator","tool_name":"get_stock_price","input":{"symbol":"NVDA"}}
  {"type":"agent_message","agent":"MarketDataInvestigator","content":"NVDA 当前价格..."}
  {"type":"system_end","agent":"System","content":"Workflow completed"}
  ```

#### A2A 调用 (以 Market Agent 为例)
- **Get Card**: `GET /a2a/marketdatainvestigator/.well-known/agent.json`
- **Run Task**: `POST /a2a/marketdatainvestigator/run`
  - **Body**: `{"message": "查询 AAPL 当前价格"}`
  - **Response**: 包含 `response` (文本结果) 和 `steps` (工具调用日志)

## 6. 开发与修改 (Development)

### 6.1 添加新 Agent

1. 在 `agent/core/agents/` 下创建新文件（如 `crypto.py`）
2. 继承 `BaseA2AAgent` 并实现 `run_task` 方法
3. 在 `agent/core/a2a_client.py` 的 `_initialize_agents` 中注册
4. Agent 会自动获得 EventBus 支持

示例：
```python
from core.agents.a2a_base import BaseA2AAgent
from core.config import Config

class CryptoA2A(BaseA2AAgent):
    def __init__(self, config: Config, event_bus=None):
        super().__init__(
            config,
            "CryptoInvestigator",
            "Analyzes cryptocurrency data",
            ["crypto_analysis"],
            [CryptoSkill()],
            CRYPTO_SYSTEM_PROMPT,
            event_bus=event_bus
        )
```

### 6.2 修改现有 Agent

- **Prompt**: 修改 `agent/core/prompts.py` 中的系统提示词
- **Tools**: 在 Agent 初始化时传入不同的 Skills
- **事件发布**: 使用 `self.publish_event(type, content, session_id, **metadata)` 发布自定义事件

### 6.3 EventBus 使用

所有 Agent 都可以通过 `self.event_bus` 发布事件：

```python
await self.publish_event(
    type="custom_event",
    content="Some message",
    session_id=task.context_id,
    custom_field="custom_value"
)
```

## 7. 注意事项 (Notes)

- **EventBus 架构**: 所有事件都通过 EventBus 传递，不要在 Agent 中直接 `yield`
- **Session ID**: 每个会话都有唯一的 `session_id`，用于隔离不同用户的事件流
- **Token Usage**: 多 Agent 协作会消耗较多 Token，建议使用低成本模型或在开发时注意
- **A2A Security**: 当前 A2A 接口未开启鉴权，生产环境需添加 Middleware 验证
- **错误处理**: 所有错误都会作为 `error` 事件发布到 EventBus

## 8. 相关文档

- [Core Module README](./core/README.md) - 核心模块详细说明
- [Agents README](./core/agents/README.md) - Agent 实现指南
- [API README](./api/README.md) - API 接口文档
