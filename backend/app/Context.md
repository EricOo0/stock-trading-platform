# 🧠 Backend Application Context

## 🎯 模块职责 (Current Scope)
本目录是后端系统的**应用层 (Application Layer)**，也是整个系统的“大脑”和“指挥中心”。
它不关心 HTTP 协议（那是 `entrypoints` 的事），也不关心数据库 SQL 怎么写（那是 `infrastructure` 的事），它只关心**业务意图的实现**。

主要职责：
1.  **Agent Orchestration**: 管理和调度各类 AI 智能体（如宏观分析、技术分析）。
2.  **Service Logic**: 处理传统的业务逻辑（如数据聚合、格式转换）。
3.  **Dependency Injection**: 通过 `registry.py` 或初始化逻辑，将底层基础设施注入到业务逻辑中。

## 🏗️ 架构与交互 (Architecture & Relationships)

### 核心组件交互图

```mermaid
graph TD
    subgraph Application Layer
        direction TB
        Orchestrator[Root Agent / Orchestrator]
        
        subgraph Specialized Agents
            Macro[Macro Agent]
            Tech[Technical Agent]
            News[News Agent]
        end
        
        subgraph Services
            MktSvc[Market Service]
            FinSvc[Fintech Service]
        end
    end

    Entrypoints --> Orchestrator
    Entrypoints --> MktSvc

    Orchestrator --> Macro
    Orchestrator --> Tech
    
    Macro -.-> MktSvc : Request Data
    Tech -.-> MktSvc : Get K-Line
```

### 关键设计模式
- **Agent-Service 混合模式**: 
    - 对于确定性任务（如“获取当前股价”），使用 `Service`。
    - 对于不确定性/推理任务（如“分析股价走势”），使用 `Agent`。
- **工厂模式**: `registry.py` 通常负责实例化 Service 单例。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 子模块索引

*   **`agents/`**: [智能体集] - 包含所有垂直领域的 AI Agent 实现。
    *   `fintech/`: 金融科技相关。
    *   `macro/`: 宏观经济分析。
    *   `market/`: 市场行情分析。
    *   `news_sentiment/`: 新闻舆情分析。
    *   `research/`: 深度投研报告生成。
    *   `technical_analysis/`: 技术指标分析。
*   **`services/`**: [业务服务] - 纯 Python 业务逻辑。
    *   `market_service.py`: 核心行情服务，聚合了多源数据。
    *   `simulation_service.py`: 模拟交易服务。

### 🔑 根目录关键文件
*   **`registry.py`**: 服务注册表，用于依赖注入和服务查找。
