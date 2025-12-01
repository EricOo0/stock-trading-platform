# Agents Directory

## 1. 模块概述

`agent/core/agents` 目录包含了系统中所有 Agent 的具体实现。每个 Agent 都实现了 A2A 协议，并通过 EventBus 发布执行进度。

## 2. Agent 列表

### 2.1 管理型 Agent

#### **Receptionist** (`receptionist.py`)
- **角色**: 接待员 / 入口
- **职责**: 分析用户输入的意图，将其转化为结构化的"研究简报"（Research Brief）
- **A2A**: 暴露为 `/a2a/receptionist`
- **事件**: `agent_start`, `agent_message`, `agent_end`
- **实现**: `ReceptionistA2A` 类，直接实现 `run_task` 方法

#### **Chairman** (`chairman.py`)
- **角色**: 主席 / 调度者
- **职责**: 负责任务规划（Planning）和路由（Routing），决定下一个执行的 Agent
- **逻辑**: 使用 `CallAgent` 工具调度 Specialist，实现完整的 ReAct 循环
- **A2A**: 暴露为 `/a2a/chairman`
- **事件**: `agent_start`, `agent_status_change`, `routing`, `agent_message`, `agent_end`
- **实现**: `ChairmanA2A` 类，自定义 ReAct 循环以精确控制事件发布

#### **Critic** (`critic.py`)
- **角色**: 评论家 / 总结者
- **职责**: 审查所有收集到的证据（Evidence），生成最终的综合回答
- **A2A**: 暴露为 `/a2a/critic`
- **事件**: `agent_start`, `agent_message`, `agent_end`
- **实现**: `CriticA2A` 类，接收 EventBus 但主要用于最终总结

### 2.2 专家型 Agent (Specialists)

所有 Specialist 都继承自 `BaseA2AAgent`，遵循 ReAct 模式，具备特定的工具集。

#### **MacroDataInvestigator** (`macro.py`)
- **技能**: 宏观经济数据查询（GDP, CPI, 利率等）
- **工具**: `MacroDataSkill`
- **A2A**: `/a2a/macrodatainvestigator`

#### **MarketDataInvestigator** (`market.py`)
- **技能**: 金融市场数据查询（股价, K线, 加密货币）
- **工具**: `MarketDataSkill`
- **A2A**: `/a2a/marketdatainvestigator`

#### **SentimentInvestigator** (`sentiment.py`)
- **技能**: 舆情与新闻情感分析
- **工具**: `SentimentAnalysisSkill`
- **A2A**: `/a2a/sentimentinvestigator`

#### **WebSearchInvestigator** (`web_search.py`)
- **技能**: 通用网络搜索，用于补充非结构化信息
- **工具**: `WebSearchSkill`
- **A2A**: `/a2a/websearchinvestigator`

## 3. 关键文件

### `a2a_base.py` - A2A Agent 基类

**类**: `BaseA2AAgent`

**功能**: 所有 Specialist Agent 的基类，提供：
- 标准化的 A2A 接口
- 自动 Agent Card 生成
- EventBus 集成
- `publish_event` 辅助方法
- 标准化的 `run_task` 实现

**使用示例**:
```python
class MySpecialistA2A(BaseA2AAgent):
    def __init__(self, config: Config, event_bus=None):
        super().__init__(
            config,
            "MySpecialist",
            "Description of what this agent does",
            ["capability1", "capability2"],
            [Skill1(), Skill2()],
            MY_SYSTEM_PROMPT,
            event_bus=event_bus
        )
```

### `utils.py` - Agent 工具函数

**关键函数**:

#### `create_agent(llm, tools, system_prompt)`
创建一个标准的 LangChain Agent Chain（Prompt + LLM + Tools）。

#### `run_react_agent(agent, tools, messages, event_bus, session_id, agent_name)`
**核心函数**。实现了一个自定义的 ReAct 循环，用于在 A2A 模式下执行 Agent。

**功能**:
- 执行 Agent 的推理-行动循环
- 自动发布事件到 EventBus：
  - `agent_status_change`: Agent 状态变化
  - `tool_call`: 工具调用详情
  - `agent_message`: Agent 最终响应
  - `error`: 执行错误
- 记录每一步的工具调用（Tool, Args, Result）

**返回值**:
```python
{
    "response": "Agent's final response",
    "steps": [
        {"tool": "ToolName", "args": {...}, "result": "..."},
        ...
    ]
}
```

## 4. EventBus 集成

所有 Agent 都通过 `event_bus` 参数接收 EventBus 实例，并使用 `publish_event` 方法发布事件。

### 事件发布模式

```python
# 在 Agent 中发布事件
await self.publish_event(
    type="agent_message",
    content="Analysis complete",
    session_id=task.context_id,
    status="speaking"
)
```

### 自动事件发布

- **BaseA2AAgent**: 自动发布 `agent_start` 和 `agent_end`
- **run_react_agent**: 自动发布 `agent_status_change`, `tool_call`, `agent_message`
- **自定义 Agent**: 可以在任何时候发布自定义事件

## 5. 如何添加新 Agent

### 方法 1: 继承 BaseA2AAgent（推荐用于 Specialist）

```python
# 1. 创建新文件 agent/core/agents/my_agent.py
from core.agents.a2a_base import BaseA2AAgent
from core.config import Config
from skills.my_skill import MySkill

MY_SYSTEM_PROMPT = """
You are a specialist in...
"""

class MyAgentA2A(BaseA2AAgent):
    def __init__(self, config: Config, event_bus=None):
        super().__init__(
            config,
            "MyAgent",
            "Description of my agent",
            ["my_capability"],
            [MySkill()],
            MY_SYSTEM_PROMPT,
            event_bus=event_bus
        )

# 2. 在 agent/core/a2a_client.py 中注册
def _initialize_agents(self):
    from core.agents.my_agent import MyAgentA2A
    
    self._agents = {
        # ... existing agents
        "myagent": MyAgentA2A(self.config, event_bus),
    }
```

### 方法 2: 自定义实现（用于特殊逻辑）

参考 `ChairmanA2A` 或 `ReceptionistA2A` 的实现，自定义 `run_task` 方法。

## 6. 调试技巧

### 查看事件流

所有事件都会被记录到日志：
```
DEBUG | core.bus:publish:44 - EventBus: Published agent_message to session_abc123
```

### 测试单个 Agent

```python
from core.agents.market import MarketA2A
from core.config import get_config
from core.bus import get_event_bus
from a2a.types import Task, TaskStatus, Message, Role, TextPart
import uuid

config = get_config()
event_bus = get_event_bus()
agent = MarketA2A(config, event_bus)

task = Task(
    id=str(uuid.uuid4()),
    context_id="test_session",
    status=TaskStatus(state="submitted"),
    history=[
        Message(
            messageId=str(uuid.uuid4()),
            role=Role.user,
            parts=[TextPart(text="查询 AAPL 股价")]
        )
    ]
)

result = await agent.run_task(task)
print(result)
```

## 7. 注意事项

- **EventBus 必需**: 所有新 Agent 都应该接受 `event_bus` 参数
- **Session ID**: 使用 `task.context_id` 作为 session_id 发布事件
- **异步方法**: 所有 `run_task` 方法都必须是 `async`
- **错误处理**: 使用 `try-except` 捕获异常并发布 `error` 事件
- **Task 对象**: 使用 `context_id` 字段（不是 `contextId`）
