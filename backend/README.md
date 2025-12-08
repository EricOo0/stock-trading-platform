# Backend Service

这是 AI 基金经理项目的后端服务模块，负责处理前端请求、数据聚合、模拟交易逻辑以及与 AI Agent 的交互。

## 架构概览

后端采用 Python 原生 `http.server` 构建的轻量级 API 服务，核心架构如下：

```mermaid
graph TD
    Frontend["Frontend (Next.js)"] <--> API_Server["API Server (api_server.py)"]
    API_Server --> Registry["Tool Registry"]
    API_Server --> SimService["Simulation Service"]
    
    Registry --> AkShare["AkShare (A股数据)"]
    Registry --> Yahoo["Yahoo Finance (美股/宏观)"]
    Registry --> Tavily["Tavily (新闻搜索)"]
    Registry --> FinTool["Financial Report Tool"]
    
    SimService --> AgentAPI["Agent System (Port 9000)"]
    SimService --> DataStore["JSON Storage"]
```

## 核心组件

### 1. API Server (`api_server.py`)
主入口文件，运行在 `8000` 端口。提供 HTTP 接口，通过 `MarketDataAPIHandler` 路由请求到相应的处理函数。

### 2. Simulation Service (`services/simulation_service.py`)
模拟交易的核心引擎。
-   **功能**：管理模拟账户、执行交易指令、聚合多因子数据 (Multi-Factor Data Aggregation)。
-   **流程**：
    1.  收集行情 (Technical)、财务 (Fundamental)、宏观 (Macro)、舆情 (Sentiment) 数据。
    2.  构造 Prompt 发送给 Agent。
    3.  解析 Agent 的 JSON 决策。
    4.  更新账户状态并记录日志。
-   **存储**：数据持久化在 `backend/data/simulations.json`。

### 3. Tool Registry (`tools/registry.py`)
工具注册表模式，统一管理所有外部数据源的调用。屏蔽了底层数据源（AkShare/Yahoo/Tavily）的差异，提供统一接口。

## API 接口文档

### 市场数据 (Market Data)
| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| `POST` | `/api/market-data` | 查询实时股票数据 |
| `GET` | `/api/market-data/hot` | 获取热门股票列表 |
| `GET` | `/api/market/historical/<symbol>` | 获取历史K线数据 |
| `GET` | `/api/market/technical/<symbol>` | 获取技术分析数据 (含MA/MACD/RSI/KDJ/BOLL) |

### 模拟交易 (Simulation)
| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| `GET` | `/api/simulation/tasks` | 获取所有模拟任务 |
| `GET` | `/api/simulation/task/<task_id>` | 获取单个任务详情 |
| `POST` | `/api/simulation/create` | 创建新模拟任务 |
| `POST` | `/api/simulation/run` | **核心接口**: 执行单日模拟回测 (Run Day) |

### 其他
| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| `POST` | `/api/tools/financial_report_tool/get_financial_indicators` | 获取财务指标 |
| `GET` | `/api/financial-report/<symbol>` |获取财报摘要 |
| `GET` | `/api/web-search` | 执行相关新闻搜索 |

## 数据流 (Data Flow)

**以 "Run Day" 为例：**
1.  **Frontend** 发起 `POST /api/simulation/run` 请求。
2.  **API Server** 接收请求，调用 `simulation_service.run_daily_simulation`。
3.  **Simulation Service** 通过 `Tools` 获取该股票的各类因子数据。
4.  **Simulation Service** 构造 Prompt，请求 Agent API (`localhost:9000`)。
5.  **Agent** 进行思考 (CoT) 并返回 JSON 决策。
6.  **Simulation Service** 执行买卖逻辑，计算 `stock_value`，更新 `simulations.json`。
7.  **Response** 返回给前端，前端更新图表和日志。

## 环境与依赖

依赖管理使用 `requirements.txt` (推荐使用 `uv` 管理)。

主要依赖：
-   `http.server` (标准库): Web 服务
-   `requests`: HTTP 客户端
-   `pandas`, `numpy`: 数据处理与指标计算
-   `akshare`: A股数据源
-   `yfinance` (可选): 美股数据
-   `ta-lib` (或手动实现的 `technical.py`): 技术指标

## 快速开始

1.  **激活环境**:
    ```bash
    source ../.venv/bin/activate
    ```

2.  **启动服务**:
    ```bash
    python api_server.py
    ```
    服务将启动在 `http://localhost:8000`。

3.  **开发调试**:
    修改代码后**需要重启服务**才能生效 (Python `http.server` 默认无热重载)。
