# AI Funding Backend

AI 基金经理项目的核心后端服务，基于 **DDD (Domain-Driven Design)** 架构重构，提供 RESTful API 以支持前端应用与 AI Agent 的交互。

## 🏗 架构概览 (Architecture)

后端采用分层架构，集成了 **Google ADK (Agent Development Kit)** 来驱动智能体。

### 核心分层 (Layers)

| 层级 | 目录 | 职责 |
| :--- | :--- | :--- |
| **Entrypoints** | `backend/entrypoints/` | **接入层**。负责接收 HTTP 请求，路由分发。 |
| **Application** | `backend/app/` | **应用层**。包含 `Agents` (智能体) 和 `Services` (业务服务)。 |
| **Domain** | `backend/domain/` | **领域层**。包含核心业务实体和纯粹的计算逻辑。 |
| **Infrastructure** | `backend/infrastructure/` | **基础设施层**。实现外部接口 (AkShare, Yahoo, Fred) 和数据库访问。 |

## 🤖 智能体体系 (Agent System)

系统内置了多个专门的 AI Agents，位于 `backend/app/agents/`：

*   **Technical Analysis Agent**: 专注于技术面分析，结合 K 线数据和技术指标（MACD, RSI 等）生成分析报告。
*   **Macro Agent**: 宏观经济分析，利用 FRED 和 AKShare 数据分析经济周期。
*   **News Sentiment Agent**: 舆情分析，通过搜索和 NLP 分析市场情绪。
*   **Research Agent**: 深度投研，负责长篇研报的生成和文档分析。
*   **Review Agent**: 负责对生成的分析结果进行审查和复盘。

*(注：根目录下的 `agent/` 目录为旧版独立服务，已被本模块内的集成 Agent 体系取代)*

## 🚀 快速开始 (Usage)

### 1. 环境准备

确保已安装 Python 3.10+ 及依赖：

```bash
# 使用 pip 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

复制 `.config.yaml` 并填入必要的 API Key：

```bash
cp .config.yaml.example .config.yaml
```

**关键配置**:
- `api_keys.tavily`: 搜索服务
- `api_keys.siliconflow` / `openai`: LLM 服务
- `api_keys.fred_api_key`: 宏观数据

### 3. 启动服务

进入项目根目录：

```bash
# 启动 API 服务 (默认端口 8000)
python -m backend.entrypoints.api.server
```

或使用开发模式（自动重载）：

```bash
python backend/dev_server.py
```

## 📚 API 文档

启动服务后，访问 Swagger UI 查看完整接口文档：
`http://localhost:8000/docs`

## 🔄 数据流示例

**行情查询流程**:
1. Frontend 发起请求 `/api/market/price`
2. `entrypoints/api/routers/market.py` 接收请求
3. 调用 `app/services/market_service.py`
4. 通过 `infrastructure/market/` 适配器 (AkShare/Yahoo) 获取数据
5. 返回标准化 JSON 数据

**智能分析流程**:
1. Frontend 发起 `/api/agent/technical/analyze` (流式)
2. `entrypoints/api/routers/agent_technical.py` 建立 SSE 连接
3. `app/services/technical_agent_service.py` 初始化 ADK Session
4. 启动 `app/agents/technical_analysis/agent.py`
5. Agent 执行 ReAct 循环，产生思考和工具调用
6. 实时将 Event 推送给前端
