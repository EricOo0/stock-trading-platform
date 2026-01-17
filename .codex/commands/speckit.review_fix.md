---
description: 拉取 MR 评论并尽可能自动修复；失败项生成 TODO。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json
  review_fetch_sh: .specify/scripts/bash/review-fetch-comments.sh
  review_apply_sh: .specify/scripts/bash/review-apply-fixes.sh
  review_summary_sh: .specify/scripts/bash/review-summary.sh
---

## 用户输入

```text
mr_id: $ARGUMENTS
```

## 概述

使用本命令，在 `/speckit.verify` 通过后、发起或合入 MR 前，拉取指定 MR 的 Code Review 评论，并尝试自动修复其中包含的代码建议。

本流程旨在自动化处理简单、明确的 CR 反馈，减少人工修复工作量，并将未自动处理的评论整理成清晰的 TODO 列表，以便开发者聚焦于需要深入讨论或复杂修改的部分。

### 步骤

1.  **环境检查与上下文准备**:
    -   调用 `.specify/scripts/bash/check-prerequisites.sh --json`，输出 `FEATURE_DIR`；加载 `plan.md` / `spec.md` / `tasks.md` 等核心设计与任务文件，确认当前特性下的实现上下文完整。
    -   从用户输入中解析 `mr_id`。

2.  **拉取 MR 评论**:
    -   调用 `{review_fetch_sh}` 脚本，并传入 `--mr-id`。
    -   该脚本会通过环境变量 `COCO_MCP_CODEBASE_CMD` 配置的命令（例如 Coco Codebase MCP 或其他 Codebase API 封装），拉取 MR 评论，并将其以 JSON 格式存储到项目本地的 `.specify/review/comments.json` 文件中。
    -   如果 `COCO_MCP_CODEBASE_CMD` 未配置，脚本会报错并退出。

3.  **应用代码修复**:
    -   调用 `{review_apply_sh}` 脚本，传入 `--comments .specify/review/comments.json` 和 `--repo-root <当前仓库根目录>`。
    -   脚本需要 `jq` 工具来解析 JSON。它会遍历 `comments.json` 中的每条评论：
        -   **对于包含代码建议的评论**：
            -   脚本会尝试将评论中的代码片段（如 suggestion fenced code block）生成为统一 diff 格式的 patch。
            -   然后使用 `git apply --reject` 尝试应用此 patch。`--reject` 选项可确保在 patch 无法完全应用时，失败的部分会保存为 `.rej` 文件，而不会污染工作目录。
            -   **应用成功后**，脚本会为这条评论的修复创建一个独立的 commit，commit message 格式为 `Address review: comment #<comment_id>`。
        -   **对于不包含代码建议或应用失败的评论**：
            -   脚本会跳过自动修复，并将这些评论标记为待办（TODO）。
    -   脚本会就地更新 `comments.json` 文件，为每条评论添加 `status`（如 "applied", "failed", "todo"）和 `status_message` 字段，记录处理结果。

4.  **生成修复总结**:
    -   调用 `{review_summary_sh}` 脚本，传入 `--comments .specify/review/comments.json`。
    -   脚本会解析更新后的 JSON 文件，输出一份简洁的总结报告，内容包括：
        -   评论总数
        -   自动修复并提交的数量
        -   尝试自动修复但失败的数量
        -   需要人工处理的 TODO 列表，并附带评论 ID 和简要说明。

5.  **后续步骤指引**:
    -   在完成以上步骤后，请仔细检查新生成的 commits，确认自动修复的逻辑符合预期。
    -   对于总结报告中列出的“失败”和“TODO”项，请手动进行修复。
    -   所有评论处理完毕后，再将当前分支推送到远端，更新 MR。

## 注意事项

-   **环境依赖**: 本流程强依赖 `jq` 工具以及一个已配置好的 `COCO_MCP_CODEBASE_CMD` 环境变量。在运行前，请确保这些依赖已满足。
-   **非破坏性操作**: `{review_apply_sh}` 脚本在应用 patch 前会检查工作目录是否干净，且每个修复都创建独立 commit，不会强制推送（force push），以保证操作历史清晰可追溯。
-   **推荐流程**: 建议在本地开发分支上运行此命令。修复完成后，通过 `git rebase -i` 或其他方式整理 commits，然后再推送到 MR 分支。
