---
description: 使用计划模板执行实现计划工作流以生成设计工件。
scripts:
  sh: .specify/scripts/bash/setup-plan.sh --json
  ps: .specify/scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: .specify/scripts/bash/update-agent-context.sh __AGENT__
  ps: .specify/scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

1.  **设置**: 运行 `.specify/scripts/bash/setup-plan.sh --json` 并解析 JSON 以获取 `FEATURE_SPEC`, `IMPL_PLAN` 等路径。
2.  **加载上下文**: 读取 `FEATURE_SPEC` 和 `.specify/.specify/memory/constitution.md`。
3.  **执行计划工作流**:
    -   填充 `IMPL_PLAN` 模板中的“技术背景”部分。
    -   在 IMPL_PLAN 中新增‘测试策略’小节，明确关键行为的单元测试覆盖范围（含边界与异常路径），作为最终 `/speckit.verify` 阶段统一执行单测的依据。
    -   生成 `research.md` (阶段 0)。
    -   生成 `data-model.md`, `contracts/`, `quickstart.md` (阶段 1)。
    -   通过运行 `.specify/scripts/bash/update-agent-context.sh __AGENT__` 更新 AI 助手上下文。
4.  **停止并报告**: 命令在阶段 2 计划后结束。报告分支、`IMPL_PLAN` 路径和生成的工件。

## 阶段

### 阶段 0: 大纲与研究

-   **从未知的技术背景中提取研究任务**。
-   **整合研究结果** 到 `research.md` 中。

### 阶段 1: 设计与合约

-   **从功能规格书中提取实体** -> `data-model.md`。
-   **从功能需求中生成 API 合约** -> `/contracts/`。
-   为关键行为制定测试策略，列出拟编写的单元测试用例与覆盖点，用于后续 `/speckit.verify` 阶段统一执行与验证。
-   **更新 AI 助手上下文**: 运行 `.specify/scripts/bash/update-agent-context.sh __AGENT__`。
