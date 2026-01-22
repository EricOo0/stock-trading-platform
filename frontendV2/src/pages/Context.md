# 📄 Frontend Pages Context

## 🎯 模块职责 (Current Scope)
本目录包含前端所有的 **页面级组件 (Page Components)**。
每个 `.tsx` 文件通常对应一个 URL 路由，充当“容器组件”的角色。

主要职责：
- **状态管理 (State)**: 初始化页面状态，调用 API 获取数据。
- **布局组装 (Layout)**: 组合 `src/components/` 中的 UI 组件。
- **路由参数 (Params)**: 读取 URL 参数 (如 `symbol`) 并传递给子组件。

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 核心页面索引

| 页面组件 | 路由 (Route) | 职责 |
| :--- | :--- | :--- |
| **`HomePage.tsx`** | `/` | **首页**。展示市场整体概况、资金流向、板块热力图。 |
| **`MarketQueryPage.tsx`** | `/market` | **市场查询**。核心功能页，包含实时 K 线、盘口数据、新闻流。 |
| **`StockAnalysisPage.tsx`** | `/analysis/:symbol` | **个股深度分析**。展示 AI 生成的深度研报、财务诊断。 |
| **`MacroDataPage.tsx`** | `/macro` | **宏观数据**。展示美联储利率、CPI、GDP 等宏观指标。 |
| **`NewsSentimentPage.tsx`** | `/news` | **舆情中心**。展示全网舆情热度排行、情绪分布。 |
| **`TechnicalAnalysisPage.tsx`** | `/technical` | **技术分析**。专注于技术指标（MACD, BOLL）的详细解读。 |
| **`TestPage.tsx`** | `/test` | **开发测试**。用于组件调试和新功能实验（非生产环境）。 |

### 🔑 交互逻辑
页面通常使用 `useEffect` 在加载时触发数据请求，并使用 `src/services/` 提供的 API 函数。
