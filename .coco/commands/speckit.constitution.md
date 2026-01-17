---
description: 根据提供的原则输入创建或更新项目章程。
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

你正在更新 `.specify/.specify/memory/constitution.md`。这个文件是一个模板，包含 `[占位符]`。

1.  **加载现有章程模板** `.specify/.specify/memory/constitution.md`。
2.  **收集占位符的值**:
    -   如果用户输入提供了值，则使用它。
    -   否则，从现有仓库上下文（README 等）推断。
    -   `CONSTITUTION_VERSION` 必须遵循语义化版本规则。
3.  **起草更新后的章程内容**:
    -   用具体文本替换每个占位符。
    -   确保每个原则部分都有简洁的名称和明确的规则。
4.  **一致性传播检查**:
    -   检查 `.specify/.specify/templates/plan-template.md`, `.specify/.specify/templates/spec-template.md`, 和 `.specify/.specify/templates/tasks-template.md` 是否与更新后的原则保持一致。
5.  **写入最终文件**:
    -   将完成的章程写回 `.specify/.specify/memory/constitution.md`。
6.  **报告完成**:
    -   向用户输出新版本、变更摘要和建议的提交信息。
