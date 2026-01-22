# 🤖 AI Agents Context

## 🎯 模块职责 (Current Scope)
本目录包含系统中所有的 **AI 智能体 (Agents)** 实现。
每个目录代表一个垂直领域的专家 Agent，它们通常具备独立的 Prompt、Tool Set (工具集) 和 Memory (记忆)。

主要职责：
- **感知 (Perception)**: 通过工具获取外部信息（搜索、查数据）。
- **推理 (Reasoning)**: 基于 LLM 进行逻辑分析和决策。
- **行动 (Action)**: 生成最终报告或触发交易信号。

## 🏗️ 架构与交互 (Architecture & Relationships)

系统支持多种 Agent 模式：

1.  **ReAct Agent**: 标准的 "Reason + Act" 循环 (如 `technical_analysis/agent.py`)。
2.  **Workflow Agent**: 基于图/状态机的固定流程 Agent (如 `research/` 中的深度研究流)。
3.  **Chat Agent**: 简单的问答型 Agent。

### 通用目录结构
大多数 Agent 目录遵循以下约定：
- `agent.py`: Agent 类定义与初始化逻辑。
- `prompts.py`: 存储 System Prompt 和 User Prompt 模板。
- `tools.py`: 定义该 Agent 专属的 Tool Function。
- `callbacks.py`: (可选) 定义流式输出的回调处理。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 专家 Agent 列表

| 目录 | 角色 | 职责 |
| :--- | :--- | :--- |
| **`technical_analysis/`** | 技术分析师 | 分析 K 线、均线、MACD/RSI 指标，给出买卖点建议。 |
| **`macro/`** | 宏观策略师 | 监控 GDP, CPI, 利率等宏观数据，判断经济周期。 |
| **`news_sentiment/`** | 舆情分析师 | 抓取新闻与社交媒体，进行 NLP 情感打分。 |
| **`research/`** | 资深研究员 | 执行 "Deep Research"，生成长篇深度研报（含目录、摘要）。 |
| **`market/`** | 市场观察员 | 负责大盘异动监控和板块轮动分析。 |
| **`fintech/`** | 金融工具人 | (旧版) 通用金融助手。 |
| **`personal_finance/`** | 私人理财顾问 | 针对用户个人资产状况提供建议。 |
| **`review/`** | 质检员 | 对其他 Agent 的产出进行查漏补缺。 |

### 🔑 关键依赖
所有 Agent 通常依赖 `backend/infrastructure/adk` (Agent Development Kit) 或 LangChain 作为底层驱动框架。
