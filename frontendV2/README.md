# AI Fund Manager - Frontend V2

现代化的 AI 基金经理前端界面，基于 **Next.js (React)** 和 **TailwindCSS** 构建。提供实时的市场数据可视化、AI 智能体流式对话以及深度的投研报告展示。

## 🚀 技术栈 (Tech Stack)

- **Framework**: React 18 + Vite (SPA Mode)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: React Hooks
- **Charting**: Lightweight Charts (TradingView) + Recharts
- **Icons**: Lucide React
- **PDF Rendering**: React-PDF

## ✨ 核心功能 (Features)

- **📊 市场仪表盘**: 实时行情、K 线图（支持 MA, MACD, RSI, KDJ, BOLL 等指标）、分时图。
- **🤖 智能体对话**: 与 AI 顾问团（技术面、宏观面、消息面专家）进行流式对话。
- **📝 深度研报**: 展示由后端生成的 PDF 研报解析、思维链 (CoT) 推理过程。
- **🕸️ 宏观监控**: 实时展示美联储利率、CPI、GDP 等核心宏观指标。

## 🛠️ 安装与运行 (Setup)

### 1. 安装依赖

```bash
npm install
```

### 2. 开发模式运行

确保后端服务已在 `http://127.0.0.1:8000` 启动。

```bash
npm run dev
```
应用将运行在 `http://localhost:3000`。

### 3. 构建生产版本

```bash
npm run build
npm run preview
```

## ⚙️ 配置 (Configuration)

主要配置位于 `vite.config.ts`，默认配置了 API 代理：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000', // 指向后端服务
      changeOrigin: true,
      secure: false,
    }
  }
}
```

## 📁 目录结构 (Directory Structure)

| Path | Description |
| :--- | :--- |
| `src/components/` | 可复用的 UI 组件 (Charts, Chat, Layout等) |
| `src/pages/` | 页面级组件 (MarketQuery, TechnicalAnalysis等) |
| `src/services/` | API 客户端服务，负责与后端通信 |
| `src/hooks/` | 自定义 React Hooks (e.g., useResearchStream) |
| `src/types/` | TypeScript 类型定义 |

## 🎨 页面概览

- **MarketQueryPage**: 核心行情查询，整合了 TradingView 图表和实时数据面板。
- **TechnicalAnalysisPage**: 专注于技术指标的深度分析。
- **MacroDataPage**: 宏观经济数据展示。
- **NewsSentimentPage**: 舆情分析与新闻聚合。
