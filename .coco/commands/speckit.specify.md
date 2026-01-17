---
description: 根据自然语言描述创建或更新功能规格书。
scripts:
  sh: .specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS"
  ps: .specify/scripts/powershell/create-new-feature.ps1 -Json "$ARGUMENTS"
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

1.  **生成一个简短的分支名称** (2-4个词)。
2.  **运行脚本 `.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS"`** 来创建新的功能分支和 `spec.md` 文件。
    -   脚本会处理分支编号和目录创建。
    -   例如: `.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS" --json --number 5 --short-name "user-auth" "添加用户认证"`
3.  **加载 `.specify/templates/spec-template.md`** 以了解所需部分。
4.  **根据用户输入填充 `spec.md`**:
    -   将占位符替换为从功能描述中派生的具体细节。
    -   重点关注 **“什么”** 和 **“为什么”**，避免 **“如何”** 实现。
    -   对于不明确的方面，做出合理的猜测，并用 `[需要澄清: 具体问题]` 标记。**最多3个澄清标记**。
    -   所有需求必须是可测试的。
    -   成功标准必须是可衡量的，并且与技术无关。
5.  **返回结果**，报告分支名称和 `spec.md` 的路径。

## 快速指引

-   专注于用户价值和业务需求。
-   为业务利益相关者而非开发人员编写。
-   避免实现细节（技术栈、API、代码结构）。
-   不要在规格书中创建任何嵌入式清单。
