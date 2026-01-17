---
description: 在任务生成后，对 spec.md, plan.md, 和 tasks.md 进行非破坏性的跨工件一致性和质量分析。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

## 目标

在实现之前，识别 `spec.md`, `plan.md`, `tasks.md` 三个核心工件之间的不一致、重复、模糊和不明确之处。此命令必须在 `/speckit.tasks` 成功生成完整的 `tasks.md` 后运行。

## 操作约束

**严格只读**: **不要**修改任何文件。输出一个结构化的分析报告。

**章程权威**: 项目章程 (`.specify/.specify/memory/constitution.md`) 在此分析范围内是**不可协商的**。

## 执行步骤

1.  **初始化分析上下文**: 运行 `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` 并解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS`。
2.  **加载工件**: 从 `spec.md`, `plan.md`, `tasks.md` 和 `constitution.md` 中加载必要的上下文。
3.  **构建语义模型**:
    -   创建需求清单、用户故事清单、任务覆盖映射和章程规则集。
4.  **执行检测**:
    -   **重复检测**: 识别几乎重复的需求。
    -   **模糊检测**: 标记模糊的形容词 (如：快、可扩展、安全) 和未解决的占位符 (TODO 等)。
    -   **不明确检测**: 标记缺少可衡量结果的需求。
    -   **章程对齐**: 检查是否与章程的 `MUST` 原则冲突。
    -   **覆盖差距**: 发现没有关联任务的需求。
    -   **不一致**: 术语不一致、数据实体不匹配、任务排序矛盾等。
5.  **分配严重性**: 将发现的问题分为 CRITICAL, HIGH, MEDIUM, LOW。
6.  **生成紧凑的分析报告**:
    -   以 Markdown 表格形式输出，包含 ID, 类别, 严重性, 位置, 摘要和建议。
7.  **提供后续操作**:
    -   如果存在 CRITICAL 问题，建议在 `/speckit.implement` 之前解决。
8.  **提供修复建议**:
    -   询问用户：“您是否希望我为前 N 个问题建议具体的修复编辑？” (不要自动应用)。
