# 🎨 Frontend Context (FrontendV2)

## 🎯 模块职责 (Current Scope)
这是 AI 基金经理系统的**新版前端 (V2)**，采用现代化的 **Single Page Application (SPA)** 架构。
它负责为用户提供直观的市场数据可视化、与 AI Agent 的流式对话交互以及深度研报的展示。

技术栈：
- **框架**: React 18 + Vite
- **语言**: TypeScript
- **样式**: TailwindCSS
- **状态管理**: React Hooks (useContext, useReducer)
- **图表**: TradingView Lightweight Charts (K线), Recharts (趋势图)

## 🏗️ 架构与交互 (Architecture & Relationships)

### 目录结构与职责划分

```mermaid
graph TD
    User[Browser] --> Router[React Router (App.tsx)]
    
    subgraph Pages [src/pages/]
        Home[HomePage]
        Market[MarketQueryPage]
        Analysis[StockAnalysisPage]
    end
    
    subgraph Components [src/components/]
        Layout[Layout/Sidebar]
        Charts[KLineChart / FinancialCharts]
        Chat[AIChatSidebar]
    end
    
    subgraph Services [src/services/]
        API[Axios Client]
    end

    Router --> Pages
    Pages --> Components
    Components --> API
    Pages --> API
    API --> Backend[Backend API (:8000)]
```

### 关键数据流
1.  **市场数据**: `MarketQueryPage` -> `services/marketService` -> Backend -> 渲染 `KLineChart`。
2.  **AI 对话**: `AIChatSidebar` -> `hooks/useResearchStream` -> Backend (SSE) -> 实时渲染 Markdown 消息。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 核心源码目录 (`src/`)

*   **`pages/`**: [页面路由] - 所有的页面级组件，与 URL 路由一一对应。
    *   `MarketQueryPage.tsx`: 核心行情看板。
    *   `StockAnalysisPage.tsx`: 个股全维度分析。
*   **`components/`**: [组件库] - 可复用的 UI 单元。
    *   `KLineChart/`: 封装 TradingView 图表库。
    *   `Council/`: AI 顾问团的“像素风”会议室动效。
    *   `research/`: 深度研报渲染组件。
*   **`services/`**: [API 客户端] - 封装对后端的 HTTP 请求，统一处理拦截器和类型定义。
*   **`types/`**: [类型定义] - TypeScript 接口定义，确保前后端数据契约一致。

### 🔑 根目录关键文件
*   **`vite.config.ts`**: Vite 构建配置，包含 `/api` 代理设置 (Proxy to Backend)。
*   **`tailwind.config.js`**: 样式主题配置。
