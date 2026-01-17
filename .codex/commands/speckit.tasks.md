---
description: 基于可用的设计工件，为功能生成一个可操作的、按依赖排序的 tasks.md。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json
  ps: .specify/scripts/powershell/check-prerequisites.ps1 -Json
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

1.  **设置**: 运行 `.specify/scripts/bash/check-prerequisites.sh --json` 并解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS`。
2.  **加载设计文档**:
    -   **必需**: `plan.md` (技术栈, 结构), `spec.md` (用户故事)。
    -   **可选**: `data-model.md`, `contracts/` 等。
3.  **执行任务生成工作流**:
    -   从 `plan.md` 和 `spec.md` 中提取信息。
    -   按用户故事生成任务。
    -   生成依赖关系图和并行执行示例。
4.  **生成 tasks.md**:
    -   使用 `.specify/templates/tasks-template.md` 作为结构。
    -   按阶段组织：设置 -> 基础 -> 用户故事 -> 润色。
    -   每个任务都必须遵循严格的清单格式。
5.  **报告**: 输出生成的 `tasks.md` 路径和摘要。

## 任务生成规则

**关键**: 任务必须按用户故事组织，以实现独立实现和测试。

### 任务配对（可选）

-   对于需要单元测试支撑的功能块，可以生成成对任务：
    -   `[Test]` 设计/补充对应单元测试（可以先列用例，再补充测试代码）；
    -   `[Impl]` 实现功能以满足上述用例描述的行为。
-   `[Test]` / `[Impl]` 只作为结构化标记，**不强制执行顺序**，也**不以 UT 是否通过作为单独任务的完成标准**。
-   单测的实际执行与结果校验在最终的 `/speckit.verify` 步骤中统一完成。

### 清单格式 (必需)

每个任务必须严格遵循此格式:

```text
- [ ] [任务ID] [P?] [故事?] 描述及文件路径
```

**示例**:

-   ✅ `- [ ] T005 [P] 在 src/middleware/auth.py 中实现认证中间件`
-   ✅ `- [ ] T012 [P] [US1] 在 src/models/user.py 中创建用户模型`
-   ✅ `- [ ] T021 [US2] [Test] 为 src/service/order.go 设计用例：创建订单的边界与异常路径`
-   ✅ `- [ ] T022 [US2] [Impl] 实现创建订单的功能逻辑（与上述单测配套）`
-   ❌ `- [ ] 创建用户模型` (缺少 ID 和故事标签)

### 任务组织

-   **按用户故事**: 每个用户故事 (P1, P2, P3...) 都有自己的阶段。
-   **从合约**: 每个合约/端点 -> 对应的用户故事。
-   **从数据模型**: 每个实体 -> 需要它的用户故事。
-   **从设置/基础设施**: 共享基础设施 -> 设置阶段。
