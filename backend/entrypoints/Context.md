# 🚪 Backend Entrypoints Context

## 🎯 模块职责 (Current Scope)
本目录是后端系统的**接入层 (Entrypoints Layer)**，是系统与外部世界（前端、管理员、定时任务）交互的唯一边界。

主要职责：
1.  **API 服务 (`api/`)**: 基于 FastAPI 暴露 RESTful 接口，处理 HTTP 请求/响应循环。
2.  **命令行工具 (`cli/`)**: 提供离线数据抓取、调试、系统验证等运维脚本。

> ⚠️ **设计原则**: 本层级**只负责**协议解析（HTTP/Args）、参数校验和路由分发，**严禁**包含任何核心业务逻辑。所有业务操作必须委托给 `backend/app/` 层执行。

## 🏗️ 架构与交互 (Architecture & Relationships)

### 模块依赖图

```mermaid
graph TD
    User[Web Frontend] --> API[API Server]
    Admin[Developer] --> CLI[CLI Tools]

    subgraph Entrypoints Layer
        API --> Routers[Routers\n(api/routers/*.py)]
        CLI --> Scripts[Debug Scripts\n(cli/debug/*.py)]
    end

    subgraph Application Layer
        Routers --> Services[App Services]
        Routers --> Agents[AI Agents]
        Scripts --> Services
    end

    API -.->|Auth Middleware| Routers
```

### 关键交互
- **Input**: 接收 HTTP Request (JSON/Form) 或 CLI 参数。
- **Process**: 
  - 验证输入数据 (Pydantic Models)。
  - 调用 `app.services` 或 `app.agents` 执行任务。
- **Output**: 返回标准化的 JSON 响应或 SSE (Server-Sent Events) 流。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 子模块索引

*   **`api/`**: [Web API]
    *   `server.py`: FastAPI 应用实例，中间件配置，CORS 设置。
    *   `routers/`: 路由定义。
        *   `agent_*.py`: 专门处理 AI 智能体的流式对话接口 (如 `agent_market.py`, `agent_research.py`)。
        *   `market.py`, `macro.py`: 传统数据查询接口。
*   **`cli/`**: [命令行]
    *   包含用于手动触发数据更新、验证数据源连通性的 Python 脚本。

### 🔑 关键文件说明

| 文件路径 | 说明 |
| :--- | :--- |
| `api/routers/adk.py` | Google ADK (Agent Development Kit) 协议的适配接口。 |
| `api/routers/agent_technical.py` | 技术面分析 Agent 的入口，处理 SSE 流式输出。 |
| `cli/login_tool.py` | 用于辅助生成或刷新 API Token 的工具。 |
