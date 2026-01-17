---
description: 基于可用的设计工件，将现有任务转换为可操作、按依赖排序的 GitHub 问题。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

1.  **运行 `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`** 并从执行的脚本中提取 **tasks.md** 的路径。
2.  **获取 Git 远程仓库地址**:
    ```bash
    git config --get remote.origin.url
    ```
    > [!CAUTION]
    > 仅当远程是 GITHUB URL 时才继续下一步

3.  对于列表中的每个任务，使用内部 Issue 创建工具在与 Git 远程仓库匹配的仓库中创建一个新问题。
    > [!CAUTION]
    > 在任何情况下都不要在与远程 URL 不匹配的仓库中创建问题。

**注意**: 此功能在内部版本中可能依赖于 Codebase 的工单系统（如 Meego）而非 GitHub Issues。
