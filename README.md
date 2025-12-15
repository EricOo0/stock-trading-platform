# AI Stock Trading Platform (AI 智能投研平台)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[English](README.md) | [中文](README_CN.md)


> [!WARNING]
> **Disclaimer**: 本项目代码完全由AI生成，暂时只跑了流程，不保证数据准确性和可靠性
> **Disclaimer**: This software is for **educational and research purposes only**. It comes with no guarantees or warranties. Using this software for live financial trading involves significant risk. The authors are not responsible for any financial losses incurred.

---

## 🇬🇧 Project Introduction
**AI Stock Trading Platform** is a comprehensive intelligent investment research system powered by multi-agent collaboration. It integrates market news analysis, fundamental screening, technical analysis, and financial report interpretation to provide investors with real-time, data-driven investment insights.

### Key Features
- **🤖 Multi-Agent Collaboration**: Specialized agents for News, Technical, and Fundamental analysis working together via a central coordinator.
- **📚 Deep Research**: Automated financial report (PDF) parsing with "Chain of Thought" reasoning and source tracing.
- **💹 Real-time Data**: Seamless integration with AkShare and YFinance for global market coverage (US/HK/A-share).
- **🕸️ Macro Insight**: Real-time macroeconomic data analysis (Fed rates, inflation) ensuring big-picture awareness.

![Project Demo Placeholder](https://via.placeholder.com/800x400?text=Project+Demo+Video+Coming+Soon)

---

## 🏗 System Architecture

The system follows a modern micro-service-like architecture with a Next.js frontend and a FastAPI backend orchestrating intelligent agents.

### Architecture Diagram

![System Architecture](assets/architecture.png)

<details>
<summary>Mermaid Source (Click to expand)</summary>

```mermaid
graph TD
    User(["User / Investor"]) --> FE["Frontend (Next.js V2)"]
    FE --> API["Backend API (FastAPI)"]
    
    subgraph "Backend Core (Python)"
        API --> Coordinator["Chairman / Coordinator Agent"]
        
        Coordinator --> NewsAgent["News & Sentiment Agent"]
        Coordinator --> TechAgent["Technical Analysis Agent"]
        Coordinator --> MacroAgent["Macro Economics Agent"]
        Coordinator --> ReportAgent["Financial Report Agent"]
        
        NewsAgent --> |"Tavily/SerpApi"| Web["Web Search"]
        TechAgent --> |"AkShare/YFinance"| MarketData["Market Data"]
        MacroAgent --> |"FRED/Search"| MacroData["Economic Data"]
        ReportAgent --> |"LlamaCloud"| PDF["PDF Parsing & RAG"]
        
        Agents --> LLM["LLM Engine (DeepSeek / OpenAI)"]
    end
    
    subgraph "Infrastructure"
        DB[("Stock Database")]
        Memory[("Redis / Vector DB")]
        LLM --> |API Call| SiliconFlow["SiliconFlow API"]
    end
```
</details>

### Directory Structure (目录结构)

| Path | Description |
| :--- | :--- |
| **`frontendV2/`** | Modern web interface (Next.js, React, TailwindCSS). Handles real-time streaming and data visualization. |
| **`backend/`** | Main backend codebase. |
| &nbsp;&nbsp;`app/agents/` | Core Agents logic (Chairman, News, Technical, Macro). |
| &nbsp;&nbsp;`infrastructure/` | Infrastructure layer (Market Data adapters, Database, LLM integrations). |
| &nbsp;&nbsp;`entrypoints/` | FastAPI server entry points and routers. |
| **`skills/`** | Shared modular capabilities (PDF Parsing, Market Data, Web Search). |
| **`memory_system/`** | Dedicated agent context management and long-term memory system (Redis/Vector DB). |

---

## 🧩 Features

| Module | Description | Implementation Method |
| :--- | :--- | :--- |
| **News Analysis**<br>(消息面分析) | Hybrid search strategy capturing market pulses. Aggregates mainstream news via Search APIs while autonomously navigating social forums using LLM-controlled browsers (**Playwright/Browser-use**) to extract retail sentiment. | **Tools**: Tavily/SerpApi (Mainstream) + Browser-use (Social)<br>**Algorithm**: Multi-source fusion & LLM Sentiment Weighting. |
| **Fundamental** | In-depth valuation analysis including PE, PB, Revenue Growth, and Profit Margins to identify undervalued assets. | **Source**: AkShare (A-share), YFinance (US/HK).<br>**Logic**: Multi-factor scoring model. |
| **Technical** | Comprehensive trend prediction integrating **Dow Theory**, **Elliott Wave**, and **Wyckoff Method**. Combines price action with quantitative indicators (**RSI, MACD, Bollinger Bands, KDJ**) for high-confidence signal generation. | **Libs**: Pandas, TA-Lib.<br>**Agent**: COT (Chain-of-Thought) reasoning with multi-theory cross-verification. |
| **Report Analysis** | Intelligent parsing of PDF Annual/Quarterly reports (10-K/10-Q) with precise citation handling. | **Engine**: LlamaCloud (Parser) + LangChain.<br>**Feature**: RAG with exact Source-Grounding (citations). |
| **Macro** | Global economic policy analysis (Fed rates, Inflation data) and its impact on asset classes. | **Data**: FRED API, Web Search.<br>**Model**: Macro-economic inference engine. |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Git](https://git-scm.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/stock-trading-platform.git
   cd stock-trading-platform
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontendV2
   npm install
   ```

4. **Configuration**
   Copy the example config and fill in your API keys:
   ```bash
   cp .config.yaml.example .config.yaml
   ```
   
   **Required API Keys**:
   - `tavily`: For AI search. ([Get Key](https://tavily.com))
   - `llama_cloud`: For high-quality PDF parsing. ([Get Key](https://cloud.llamaindex.ai))
   - `siliconflow` or `openai`: Main LLM provider.
   - `fred_api_key`: For macroeconomic data.

5. **Run the System**
   
   Start Backend:
   ```bash
   # In root directory
   python -m backend.entrypoints.api.server
   ```
   
   Start Frontend:
   ```bash
   # In frontendV2 directory
   npm run dev
   ```
   Access the app at `http://localhost:3000`.

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feat/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feat/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📅 Roadmap
