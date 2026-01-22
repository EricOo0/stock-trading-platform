# 📡 Frontend Services Context

## 🎯 模块职责 (Current Scope)
本目录是前端的 **API 客户端层 (API Client Layer)**。
它负责与后端 RESTful API 进行通信，封装了所有的 HTTP 请求细节。

主要职责：
- **HTTP 封装**: 统一管理 Axios 实例、Base URL、请求/响应拦截器。
- **类型安全**: 定义 API 请求参数和响应数据的 TypeScript 接口。
- **错误处理**: 统一处理网络错误和业务异常。

## 🏗️ 架构与交互 (Architecture & Relationships)

### 调用链路
`Component/Page` -> `Service Function` -> `Axios Instance` -> `Backend API`

## 🗺️ 导航与细节 (Navigation & Drill-down)

### 📂 服务模块索引

| 文件 | 对应后端模块 | 职责 |
| :--- | :--- | :--- |
| **`marketService.ts`** | `market_service` | 获取股票实时报价、K线历史、板块数据。 |
| **`stockAPI.ts`** | `market_service` | (辅助) 股票列表搜索、元数据查询。 |
| **`agentAPI.ts`** | `agent_router` | 触发 AI Agent 任务（非流式部分），获取 Agent 状态。 |
| **`macroAPI.ts`** | `macro_service` | 获取宏观经济指标数据。 |
| **`newsSentimentAPI.ts`** | `news_service` | 获取新闻列表、情感分析结果。 |
| **`simulationAPI.ts`** | `simulation_service` | 管理模拟交易账户、订单提交。 |
| **`memoryService.ts`** | `memory_system` | (可选) 直接与独立记忆服务交互。 |

### 🔑 关键代码模式
所有 Service 函数通常返回 `Promise<T>`，其中 `T` 是在 `src/types/` 中定义的强类型接口。

```typescript
// 示例
export const getStockPrice = async (symbol: string): Promise<StockPrice> => {
  const response = await api.get(\`/market/price/\${symbol}\`);
  return response.data;
};
```
