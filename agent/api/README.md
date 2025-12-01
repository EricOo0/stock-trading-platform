# Agent API Module

## 1. 模块概述

`agent/api` 目录负责系统的对外接口，包括标准的 RESTful API 和 Google A2A 协议实现。

## 2. 文件说明

### 2.1 `routes.py` - REST API

**功能**: 提供给前端或常规客户端使用的标准接口。

**Endpoints**:

#### `POST /api/chat` - 同步对话
- **Request**: 
  ```json
  {
    "message": "分析 NVDA 股价",
    "session_id": "optional_session_id"
  }
  ```
- **Response**: 
  ```json
  {
    "response": "完整的分析结果",
    "session_id": "session_abc123",
    "tool_calls": [...],
    "success": true
  }
  ```

#### `POST /api/chat/stream` - 流式对话 ⭐ 推荐
- **Request**: 
  ```json
  {
    "message": "分析 NVDA 股价"
  }
  ```
- **Response**: NDJSON 事件流
  ```json
  {"type":"agent_start","agent":"Receptionist","content":"Analyzing...","timestamp":123456789.0}
  {"type":"agent_message","agent":"Receptionist","content":"Research brief..."}
  {"type":"routing","from":"Chairman","to":"MarketDataInvestigator","instruction":"..."}
  {"type":"tool_call","agent":"MarketDataInvestigator","tool_name":"get_stock_price"}
  {"type":"agent_message","agent":"MarketDataInvestigator","content":"NVDA price is..."}
  {"type":"system_end","agent":"System","content":"Workflow completed"}
  ```
- **Media Type**: `application/x-ndjson`
- **特点**: 
  - 实时返回 Agent 执行进度
  - 通过 EventBus 订阅事件流
  - 支持前端实时 UI 更新

#### `POST /api/config` - 更新配置
- **功能**: 动态更新系统配置（API Key, Model 等）
- **Request**: 
  ```json
  {
    "api_key": "new_key",
    "model": "gpt-4",
    "temperature": 0.7
  }
  ```

#### `GET /api/tools` - 列出可用工具
- **Response**: 
  ```json
  {
    "tools": [
      {"name": "MacroDataInvestigator", "description": "..."},
      {"name": "MarketDataInvestigator", "description": "..."}
    ]
  }
  ```

#### `GET /api/health` - 健康检查
- **Response**: `{"status": "healthy"}`

### 2.2 `a2a.py` - A2A 协议实现

**功能**: 实现 Google Agent-to-Agent (A2A) 协议，使每个内部 Agent 都能独立对外服务。

**实现细节**:
- 每个 Agent 都有独立的 A2A 端点
- 支持标准的 Agent Card 和 Task 执行接口
- 自动集成 EventBus

**Endpoints 格式**: `/a2a/{agent_name}/...`

#### Agent Card
- **Endpoint**: `GET /a2a/{agent_name}/.well-known/agent.json`
- **示例**: `GET /a2a/marketdatainvestigator/.well-known/agent.json`
- **Response**: 
  ```json
  {
    "name": "MarketDataInvestigator",
    "description": "Analyzes stock and crypto market data",
    "version": "1.0.0",
    "capabilities": {"skills": ["market_analysis"]},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "url": "http://localhost:8001/a2a/marketdatainvestigator"
  }
  ```

#### Task Execution
- **Endpoint**: `POST /a2a/{agent_name}/run`
- **Request**: 
  ```json
  {
    "message": "查询 AAPL 当前价格"
  }
  ```
- **Response**: 
  ```json
  {
    "response": "AAPL 当前价格为 $150.25",
    "steps": [
      {
        "tool": "get_stock_price",
        "args": {"symbol": "AAPL"},
        "result": "Price: $150.25"
      }
    ]
  }
  ```

**可用的 A2A Agents**:
- `/a2a/receptionist`
- `/a2a/chairman`
- `/a2a/macrodatainvestigator`
- `/a2a/marketdatainvestigator`
- `/a2a/sentimentinvestigator`
- `/a2a/websearchinvestigator`
- `/a2a/critic`

### 2.3 `models.py` - 数据模型

**功能**: 定义 API 请求和响应的 Pydantic 模型。

**关键模型**:
- `ChatRequest`: 对话请求
- `ChatResponse`: 对话响应
- `ToolCall`: 工具调用记录
- `ConfigUpdateRequest`: 配置更新请求
- `HealthResponse`: 健康检查响应

## 3. 流式 API 详解

### 3.1 工作原理

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    agent = get_agent()
    
    async def event_generator():
        import json
        # agent.stream_run() 订阅 EventBus 并 yield 事件
        async for event in agent.stream_run(request.message):
            yield json.dumps(event) + "\n"
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
```

### 3.2 事件类型

| 事件类型 | 说明 | 示例 |
|---------|------|------|
| `agent_start` | Agent 开始工作 | `{"type":"agent_start","agent":"Chairman","status":"thinking"}` |
| `agent_message` | Agent 发送消息 | `{"type":"agent_message","agent":"Critic","content":"Final analysis..."}` |
| `agent_status_change` | Agent 状态变化 | `{"type":"agent_status_change","agent":"Market","status":"speaking"}` |
| `routing` | Chairman 路由 | `{"type":"routing","from":"Chairman","to":"Market","instruction":"..."}` |
| `tool_call` | 工具调用 | `{"type":"tool_call","agent":"Market","tool_name":"get_price"}` |
| `agent_end` | Agent 完成 | `{"type":"agent_end","agent":"Market","status":"completed"}` |
| `error` | 错误 | `{"type":"error","agent":"System","content":"Error message"}` |
| `system_end` | 工作流完成 | `{"type":"system_end","agent":"System"}` |

### 3.3 前端集成示例

```javascript
const response = await fetch('http://localhost:8001/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: "Analyze NVDA" })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        handleEvent(event); // 处理事件
    }
}
```

## 4. 开发指南

### 4.1 添加新的 REST API 路由

在 `routes.py` 中添加新的端点：

```python
@router.post("/api/new-endpoint")
async def new_endpoint(request: NewRequest):
    # 实现逻辑
    return {"result": "..."}
```

### 4.2 添加新的 A2A Agent

1. 在 `core/agents/` 中实现 Agent
2. 在 `core/a2a_client.py` 中注册
3. A2A 端点会自动生成

### 4.3 修改事件流

事件流由 `agent.stream_run()` 和各个 Agent 的 `publish_event` 控制。

要添加新的事件类型：
1. 在 Agent 中调用 `self.publish_event(type="new_type", ...)`
2. 更新前端事件处理逻辑

## 5. 注意事项

- **CORS**: 生产环境需要配置 CORS 中间件
- **认证**: 当前未实现认证，生产环境需添加
- **限流**: 建议添加 rate limiting
- **错误处理**: 所有端点都有 try-except 包装
- **日志**: 使用 loguru 记录所有请求和错误
