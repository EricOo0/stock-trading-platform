# Agent Core Module

## 1. 模块概述

`agent/core` 目录包含了多 Agent 系统的核心业务逻辑、事件总线和 A2A 协议集成。它是整个系统的"大脑"。

## 2. 核心组件

### 2.1 `agent.py` - 主编排器

**类**: `StockAnalysisAgent`

**功能**: 系统的对外门面（Facade）。负责初始化 A2A 客户端，处理 `run` 和 `stream_run` 请求。

**关键方法**:
- `__init__(config)`: 初始化 Agent 和 A2A 客户端
- `run(query, memory)`: 执行一次完整的对话（非流式）
- `stream_run(query)`: **流式执行**，通过 EventBus 返回实时事件流

**工作流程**:
```python
async def stream_run(self, query: str):
    # 1. 创建 session_id
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    # 2. 获取 EventBus
    event_bus = get_event_bus()
    
    # 3. 在后台启动 Agent 管道
    async def run_pipeline():
        # Receptionist -> Chairman -> Specialists -> Critic
        ...
    
    asyncio.create_task(run_pipeline())
    
    # 4. 订阅 EventBus 并 yield 事件
    async for event in event_bus.subscribe(session_id):
        yield event_dict
```

### 2.2 `bus.py` - 事件总线 ⭐ NEW

**类**: `EventBus`

**功能**: 中央事件总线，实现发布-订阅模式，解耦 Agent 执行和事件流式传输。

**核心方法**:
- `publish(event: Event)`: 发布事件到指定 session
- `subscribe(session_id: str)`: 订阅指定 session 的事件流
- `close_session(session_id: str)`: 关闭 session 并清理资源

**Event 结构**:
```python
@dataclass
class Event:
    type: str           # 事件类型
    session_id: str     # 会话 ID
    agent: str          # 发布事件的 Agent
    content: str        # 事件内容
    timestamp: float    # 时间戳
    metadata: dict      # 额外元数据
```

**使用示例**:
```python
from core.bus import get_event_bus, Event

event_bus = get_event_bus()

# 发布事件
await event_bus.publish(Event(
    type="agent_message",
    session_id="session_abc123",
    agent="Chairman",
    content="Planning next step...",
    metadata={"status": "thinking"}
))

# 订阅事件
async for event in event_bus.subscribe("session_abc123"):
    print(event)
```

### 2.3 `a2a_client.py` - A2A 客户端

**类**: `A2AAgentClient`

**功能**: 管理所有 A2A Agent 实例，提供统一的调用接口。

**关键方法**:
- `_initialize_agents()`: 初始化所有 Agent 并注入 EventBus
- `call_agent(agent_name, message, session_id)`: 调用指定 Agent
- `_create_task(message, session_id)`: 创建 A2A Task 对象

**Agent 注册**:
```python
def _initialize_agents(self):
    event_bus = get_event_bus()
    
    self._agents = {
        "receptionist": ReceptionistA2A(self.config, event_bus),
        "chairman": ChairmanA2A(self.config, event_bus),
        "macro": MacroA2A(self.config, event_bus),
        "market": MarketA2A(self.config, event_bus),
        # ...
    }
```

### 2.4 `config.py` - 配置管理

**类**: `Config`, `LLMConfig`, `SkillsConfig`, etc.

**功能**: 使用 Pydantic 管理系统配置，支持从 YAML 文件加载。

**配置文件**: `agent/config.yaml`

### 2.5 `memory.py` - 对话记忆

**类**: `ConversationMemory`, `MemoryManager`

**功能**: 管理多会话的对话历史，支持会话隔离和持久化。

### 2.6 `state.py` - 状态定义

**类**: `AgentState` (TypedDict)

**功能**: 定义 Agent 运行时的全局状态（主要用于旧的 LangGraph 架构，新架构中已较少使用）。

### 2.7 `prompts.py` - 系统提示词

**功能**: 集中管理所有 Agent 的 System Prompts。

**包含的提示词**:
- `RECEPTIONIST_SYSTEM_PROMPT`
- `CHAIRMAN_SYSTEM_PROMPT`
- `MACRO_AGENT_SYSTEM_PROMPT`
- `MARKET_AGENT_SYSTEM_PROMPT`
- `SENTIMENT_AGENT_SYSTEM_PROMPT`
- `WEB_SEARCH_AGENT_SYSTEM_PROMPT`
- `CRITIC_SYSTEM_PROMPT`

## 3. Agent 实现 (`agents/` 目录)

### 3.1 `a2a_base.py` - A2A Agent 基类

**类**: `BaseA2AAgent`

**功能**: 所有 Specialist Agent 的基类，提供标准的 A2A 接口和 EventBus 集成。

**核心功能**:
- 自动创建 Agent Card
- 标准化的 `run_task` 实现
- 内置 `publish_event` 方法
- ReAct 循环集成

**使用方式**:
```python
class MyAgent(BaseA2AAgent):
    def __init__(self, config: Config, event_bus=None):
        super().__init__(
            config,
            "MyAgent",
            "Description",
            ["skill1", "skill2"],
            [Skill1(), Skill2()],
            MY_SYSTEM_PROMPT,
            event_bus=event_bus
        )
```

### 3.2 `utils.py` - Agent 工具函数

**关键函数**:
- `create_agent(llm, tools, system_prompt)`: 创建 LangChain Agent
- `run_react_agent(agent, tools, messages, event_bus, session_id, agent_name)`: 运行 ReAct 循环并发布事件

**事件发布**:
`run_react_agent` 会自动发布以下事件：
- `agent_status_change`: Agent 状态变化
- `tool_call`: 工具调用
- `agent_message`: Agent 消息

### 3.3 具体 Agent 实现

#### `receptionist.py` - 接待员
- **功能**: 分析用户意图，生成研究简报
- **事件**: `agent_start`, `agent_message`, `agent_end`

#### `chairman.py` - 主席
- **功能**: 规划任务，路由到 Specialist，调用 Critic
- **事件**: `agent_start`, `agent_status_change`, `routing`, `agent_message`, `agent_end`
- **特殊**: 实现了完整的 ReAct 循环，管理整个调查流程

#### `critic.py` - 评论家
- **功能**: 综合所有证据，生成最终回答
- **事件**: `agent_start`, `agent_message`, `agent_end`

#### Specialist Agents
- `macro.py`: 宏观经济数据分析
- `market.py`: 市场行情数据查询
- `sentiment.py`: 新闻情感分析
- `web_search.py`: 通用网络搜索

所有 Specialist 都继承自 `BaseA2AAgent`，自动获得 EventBus 支持。

## 4. 数据流详解

### 4.1 完整执行流程

```
1. 用户请求 → API /chat/stream
2. agent.stream_run(query) 创建 session_id
3. 后台启动 run_pipeline():
   a. Receptionist.run_task() → 发布事件 → EventBus
   b. Chairman.run_task() → 发布事件 → EventBus
      - Chairman 调用 Specialist → 发布事件 → EventBus
      - Specialist 调用工具 → 发布事件 → EventBus
      - 循环直到完成
   c. Critic.run_task() → 发布事件 → EventBus
4. stream_run() 订阅 EventBus → yield 事件到前端
5. 前端接收 NDJSON 事件流 → 更新 UI
```

### 4.2 EventBus 会话隔离

每个用户请求都有独立的 `session_id`，EventBus 使用 session-scoped channels 确保事件不会混淆：

```python
# EventBus 内部
self._channels: Dict[str, asyncio.Queue] = {}

def _get_channel(self, session_id: str) -> asyncio.Queue:
    if session_id not in self._channels:
        self._channels[session_id] = asyncio.Queue()
    return self._channels[session_id]
```

## 5. 扩展指南

### 5.1 添加新的事件类型

在 Agent 中发布自定义事件：

```python
await self.publish_event(
    type="custom_progress",
    content="Processing step 3/10",
    session_id=task.context_id,
    progress=30,
    step=3,
    total=10
)
```

前端需要相应地处理这个新事件类型。

### 5.2 修改 Agent 行为

1. **修改提示词**: 编辑 `prompts.py`
2. **修改工具**: 在 Agent 初始化时传入不同的 Skills
3. **修改逻辑**: 重写 Agent 的 `run_task` 方法

### 5.3 调试 EventBus

EventBus 会记录所有发布的事件：

```python
logger.debug(f"EventBus: Published {event.type} to {event.session_id}")
```

可以通过日志追踪事件流。

## 6. 注意事项

- **异步编程**: 所有 Agent 方法都是 `async`，注意使用 `await`
- **EventBus 单例**: EventBus 是全局单例，通过 `get_event_bus()` 获取
- **Session 清理**: 完成后调用 `event_bus.close_session(session_id)` 清理资源
- **错误处理**: 所有异常都应该作为 `error` 事件发布，而不是直接抛出
- **Task 对象**: A2A Task 使用 `context_id` 字段（不是 `contextId`）

## 7. 废弃的组件

以下组件已被 EventBus 架构替代，不再使用：
- `graph.py`: 旧的 LangGraph 图定义（保留用于参考）
- `nodes.py.deprecate`: 旧的节点定义
- `agent.py.backup.deprecate`: 旧的 Agent 实现

新架构不再使用 LangGraph 的图编排，而是通过 A2A 协议和 EventBus 实现更灵活的 Agent 协作。
