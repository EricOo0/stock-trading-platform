# 🧩 Frontend Components Context

## 🎯 模块职责 (Current Scope)
本目录包含前端应用的所有 **UI 组件 (Components)**。
组件按**功能领域 (Domain)** 而非技术类型进行组织，以提高可维护性。

主要职责：
- **展示 (Presentation)**: 接收 Props 并渲染 UI。
- **交互 (Interaction)**: 处理用户点击、输入事件。
- **复用 (Reusability)**: 封装通用逻辑（如 K 线图、聊天框）。

## 🏗️ 架构与交互 (Architecture & Relationships)

### 组件分类
1.  **基础组件 (Base)**: 如 `Layout/`，提供全局结构。
2.  **业务组件 (Business)**: 如 `Financial/`, `Council/`，与特定业务强耦合。
3.  **图表组件 (Charts)**: 如 `KLineChart/`，封装第三方图表库。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 组件目录索引

| 目录 | 职责 | 关键文件 |
| :--- | :--- | :--- |
| **`Layout/`** | 全局布局 | `Sidebar.tsx` (侧边导航), `Header.tsx` (顶部栏) |
| **`KLineChart/`** | K线图表 | `TradingViewKLineChart.tsx` (TradingView 核心封装) |
| **`Council/`** | AI 顾问团 | `CouncilRoom.tsx` (像素风会议室), `PixelChatLog.tsx` |
| **`AIChat/`** | 对话交互 | `AIChatSidebar.tsx` (流式对话侧边栏) |
| **`Financial/`** | 财务数据 | `FinancialIndicatorsDisplay.tsx` (财务指标卡片) |
| **`MarketQuery/`** | 行情看板 | `RealTimeDataPanel.tsx` (实时盘口) |
| **`research/`** | 深度研报 | `DeepResearchCard.tsx` (研报概览), `artifacts/` (图表渲染器) |

### 🔑 设计模式
- **Smart/Dumb Components**: 大多数 `pages/` 是 Smart 组件（处理逻辑），而 `components/` 主要是 Dumb 组件（只负责渲染）。
- **Props Drilling**: 尽量避免深层 Props 传递，复杂状态推荐使用 Context。
