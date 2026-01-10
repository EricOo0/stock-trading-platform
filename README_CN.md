# AI Stock Trading Platform (AI 智能投研平台)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | [中文](README_CN.md)

> [!WARNING]
> **Disclaimer**: 本项目是一次 **AI Vibe Coding** 实践，旨在探索 AI 能否独立完成一个大型项目的编写与维护。**所有代码均由 AI 生成**。
>
> **免责声明**: 本软件仅供**教育和研究使用**。部分数据可能存在问题或延迟。不提供任何保证。使用本软件进行实盘交易涉及巨大风险，作者不对任何资金损失负责。
>
> **注意**: 部分数据源 (如 Yahoo Finance) 可能需要**科学上网**环境才能正常访问。如果您在中国大陆地区使用，请确保配置了合适的网络代理，否则可能会导致数据获取失败。

---

## 💡 项目背景 (Background)

这个项目的核心目的是进行一次 **AI 全栈开发实践**。我们试图回答一个问题：**目前的 AI 技术能否在极少人为干预的情况下，自主完成一个包含前端、后端、数据处理和复杂逻辑的大型软件系统的编写与维护？**

因此，本项目从架构设计、代码编写到文档撰写，绝大部分工作均由 AI 完成。

---

## 🏗 系统架构 (System Architecture)

项目整体分为三个核心部分，后端集成了多种 Agent 范式（ReAct, Multi-Agent Debate, Master-Sub Agent）和框架（Google ADK, LangChain）：

1.  **前端 (Frontend)**: 负责数据展示与用户交互，提供现代化的可视化界面。
2.  **后端 (Backend)**: 负责数据拉取、处理以及核心的 Agent 调度与编排。
3.  **记忆系统 (Memory System)**: 独立的认知存储层，由短期、中期、长期记忆组成，旨在让 AI 形成长期投资风格并具备自我反思能力。

---

## 🧩 功能模块 (Features)

### 1. 首页 (Home)
项目入口，提供直观的市场数据展示，包括 A 股大盘指数、板块资金流向等关键信息，帮助用户快速把握市场整体热度。

![首页](assets/2026.1.10/首页-市场数据.png)

### 2. 个股分析 (Stock Analysis)
针对单只股票的全方位深度扫描，包含以下子模块：

*   **行情复盘**: 展示股票基本信息，AI 针对今日股价涨跌情况进行复盘分析，并给出操作建议。
    ![行情复盘](assets/2026.1.10/个股分析-行情复盘.png)

*   **技术分析**: 结合 MACD、KDJ、BOLL 等技术指标以及道氏理论等经典交易理论，AI 对盘面进行深度解读，预测后市走势。
    ![技术分析](assets/2026.1.10/个股分析-技术分析.png)

*   **消息面分析**: 全网搜索主流媒体新闻，并深入 Reddit、雪球等社交媒体挖掘散户讨论，通过 AI 进行情感与舆情分析。
    ![消息面分析](assets/2026.1.10/个股分析--消息面分析.png)

*   **财报解读**: 自动拉取并解析财报数据，进行基本面诊断，评估公司财务健康状况。
    ![财报解读](assets/2026.1.10/个股分析-财报解读.png)

*   **深度投研**: 综合上述所有工具的分析结果，对股票进行全面的综合评分与深度研判。
    ![深度投研](assets/2026.1.10/个股分析-深度投研.png)

*   **模拟回测**: (实验性功能) 基于 AI 策略的历史回测展示。
    ![模拟回测](assets/2026.1.10/个股分析模拟回测.png)

### 3. 宏观数据 (Macro Data)
实时拉取国内外核心宏观经济数据（如 CPI, PPI, GDP, 恐慌指数 VIX 等），AI 基于这些数据进行宏观经济形势分析，辅助判断大类资产配置方向。

![宏观数据](assets/2026.1.10/宏观数据.png)

### 4. AI 顾问团 (AI Council)
参考“一人公司”理念，构建由多个 AI 角色（如 CEO、CTO、首席分析师等）组成的顾问团队。用户提出问题，多个 AI 各司其职进行圆桌讨论，最终给出综合结论。

![AI 顾问团](assets/2026.1.10/AI顾问团.png)

### 5. 记忆可视化 (Memory Visualization)
这是项目的一个探索性亮点。我们期望 AI 不仅仅是无状态的问答机器，而是能够形成长期的投资风格。
*   **反思与修正**: AI 能对历史决策进行复盘和反思，修正自己的投资逻辑。
*   **三层记忆**: 实现了由短期记忆（Working Memory）、中期记忆（Episodic Memory）和长期记忆（Semantic Memory）组成的记忆系统。
*(注：目前仅有少量 Agent 接入此系统)*

![记忆可视化](assets/2026.1.10/记忆可视化.png)

---

## 🛠️ 技术探索 (Technical Exploration)

本项目在后端 Agent 的开发中进行了广泛的技术探索：

*   **Agent 范式多样性**:
    *   **Single Agent ReAct**: 用于简单的工具调用任务。
    *   **Multi-Agent Debate**: 用于复杂问题的多视角探讨（如顾问团）。
    *   **Master-Sub Agent**: 用于任务拆解与分发（如深度投研）。
*   **框架尝试**:
    *   **Google ADK (Agent Development Kit)**: 用于构建标准化 Agent。
    *   **LangChain**: 用于早期的原型验证和部分工具链。
    *   **自研 EventBus**: 实现各模块间的解耦与通信。

---

## 🚀 快速开始

### 1. 启动 Backend & Agent 服务

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境 (复制 .config.yaml.example 并填入 API Key)
cp .config.yaml.example .config.yaml

# 启动核心 API 服务
python -m backend.entrypoints.api.server
```

### 2. 启动 Memory System (可选)

```bash
cd memory_system
pip install -r requirements.txt
python -m api.server
```

### 3. 启动 Frontend

```bash
cd frontendV2
npm install
npm run dev
# 访问 http://localhost:3000
```

---

## 🤝 贡献

欢迎 Fork 本项目并提交 PR。由于代码主要由 AI 生成，可能会包含一些非典型的编码习惯，欢迎人类开发者进行优化！

## 📄 许可证

MIT License
