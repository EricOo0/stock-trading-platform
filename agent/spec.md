# Project Specification: Multi-Agent Transformation

## 1. 目标 (Goals)
将现有的单体 ReAct Agent 改造为基于 **LangGraph** 的 **多 Agent 协作系统**。系统需具备动态任务拆解、多角色专业分工、信息共享和多轮迭代推理的能力。

## 2. 功能规范 (Functional Specifications)

### 2.1 角色与能力
*   **Business Manager**:
    *   必须具备基于 Context 动态选择下一个 Speaker 的能力。
    *   必须具备识别 "FINISH" 状态的能力。
    *   输出必须包含对用户问题的最终完整回答。
*   **Worker Agents**:
    *   **Macro Agent**: 支持查询 GDP, CPI, 利率, 汇率等宏观指标。
    *   **Market Agent**: 支持查询 股票/加密货币 价格, 历史K线, 简单技术指标。
    *   **Sentiment Agent**: 支持查询并分析最近 3-7 天的新闻情感。
    *   **Web Search Agent**: 支持通用关键词搜索，并总结前 5-10 条结果。

### 2.2 协作机制 (Collaboration)
*   **通信协议**: Agent 之间通过共享的 `AgentState` (Message History) 进行通信，无需点对点私聊。
*   **路由逻辑**: 采用 LLM 决策路由 (Router)，而非硬编码的顺序流。
*   **防死循环**: 必须设置 `recursion_limit` (默认 20 轮)，防止讨论无限进行。

### 2.3 状态管理 (State Management)
*   系统需维护一个全局 `messages` 列表，包含：
    *   `HumanMessage`: 用户输入。
    *   `AIMessage`: 各 Agent 的发言（需标记 `name` 字段以区分角色）。
    *   `FunctionMessage`: 工具调用结果。

## 3. 非功能规范 (Non-Functional Specifications)

*   **响应时间**: 单次 Agent 交互 (LLM推理+工具调用) 建议在 3-5 秒内，复杂任务总耗时不超过 60 秒。
*   **鲁棒性**:
    *   单个 Agent 工具调用失败不应导致整个系统崩溃，应返回错误提示并允许 Manager 尝试其他路径。
    *   LLM 输出格式解析失败应有重试机制。
*   **可扩展性**: 架构应支持通过添加新的 Node 和 Edge 轻松增加新的 Agent 角色。
*   **日志**: 必须记录详细的 Graph 执行路径和每个 Node 的输入输出，便于调试。

## 4. 接口规范 (API Specifications)

*   **Input**:
    ```json
    {
      "query": "string",
      "chat_history": "list[message]"
    }
    ```
*   **Output**:
    ```json
    {
      "response": "string", // 最终汇总回答
      "intermediate_steps": [ // 中间思考过程 (可选，用于前端展示)
        {
          "agent": "MarketAgent",
          "action": "Check Price",
          "content": "..."
        },
        ...
      ]
    }
    ```
