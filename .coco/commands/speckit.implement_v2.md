---
description: 并行执行无依赖任务，基于 Coco subAgent 与 git worktree。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  worktree_create_sh: .specify/scripts/bash/worktree-create.sh
  task_merge_sh: .specify/scripts/bash/task-merge.sh
  worktree_clean_sh: .specify/scripts/bash/worktree-clean.sh
  task_status_sh: .specify/scripts/bash/task-status.sh
agent_scripts:
  sh: .specify/scripts/bash/update-agent-context.sh __AGENT__
---

## 概述

1.  **前置检查**: 运行 `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` 确认 `tasks.md` 等上下文就绪。
2.  **并行任务识别**:
    -   解析 `tasks.md`，将标记为 `[P]` 或未显式声明依赖的任务识别为可并行任务。
    -   根据用户故事或模块（如 `[US1]`, `[US2]`）对可并行任务进行分组。无用户故事的任务可独立成组。
3.  **Git Worktree 工作流（脚本优先）**:
    -   **创建基础分支与任务分支**: 使用 `.specify/scripts/bash/worktree-create.sh` 创建基础分支（例如 `feat/<slug>` 或 `fix/<slug>`）以及每个任务组的分支（例如 `feat/<slug>-task-<ID>`），必要时结合 `--base` 和 `--remote` 参数。推荐始终使用 `feat/`、`fix/`、`chore/` 作为前缀，并让 `<slug>` 保持与需求/用户故事一致的语义。
    -   **为每个任务组创建 Worktree**: 通过 `worktree-create.sh --branch feat/<slug>-task-<ID> --path .worktrees/<ID>` 为每个任务组创建独立 worktree（例如 `.worktrees/T021`）。在生成的 Agent 命令中，这些脚本路径会被重写为 `.specify.specify/.specify/scripts/bash/...`，可直接由 AI 调用。
    -   **状态查看与清理**:
        -   使用 `.specify/scripts/bash/task-status.sh --path .worktrees/<ID>` 查看当前 worktree 的分支与改动摘要。
        -   在任务合入完成后，使用 `.specify/scripts/bash/worktree-clean.sh --path .worktrees/<ID> --branch feat/<slug>-task-<ID>`（必要时加 `--force`）移除 worktree 并按策略清理本地分支。
    -   **安全说明**: 所有 git 操作默认通过这些脚本完成，以减少误操作风险；脚本内部统一避免 rebase/force push，并在删除分支前进行合并检查。

## 分支命名规范

-   推荐所有开发分支遵循「前缀 + 语义化后缀」的命名方式：
    -   新功能：`feat/<语义化-slug>`，例如 `feat/user-auth-migration`。
    -   缺陷修复：`fix/<语义化-slug>`，例如 `fix/order-calc-bug`。
    -   杂项 / 脚本 / CI 调整：`chore/<语义化-slug>`，例如 `chore/ci-pipeline-tidy`。
-   当从同一个需求或用户故事拆分出多个任务分支时，可以在上述基础分支名后追加任务标识，例如：
    -   基础特性分支：`feat/user-auth-migration`
    -   任务分支：`feat/user-auth-migration-task-T021`、`feat/user-auth-migration-task-T022`。
-   使用 `.specify/scripts/bash/worktree-create.sh` 创建分支时，只需要将 `--branch` 参数设置为符合上述规范的名字（如 `--branch feat/user-auth-migration-task-T021`）；脚本本身对分支前缀没有特殊要求。
4.  **Coco subAgent 编排 (并行执行)**:
    -   **并发限制**: 默认最多并行启动 3 个 subAgent。若任务间存在依赖，则退化为串行执行。
    -   **创建/指定 subAgent**: 为每个任务组创建或指定一个 subAgent，命名为 `subagent-<ID>`。
    -   **任务分发**: 使用 `@subagent-<ID>` mention，向其分发任务组。上下文需包含：
        -   **Worktree 路径**: e.g., `.worktrees/<ID>`。
        -   **任务 ID** 和 `tasks.md` 的相关摘录。
        -   设计文档摘录，如 `plan.md`, `contracts/`, `data-model.md`。
    -   **推荐工具集**:
        -   **必需**: `files.read`, `files.write_file`。
        -   **可选**: `bash`（用于 `go generate` 等）；**不要**在本命令中调用任何 UT 相关工具或 Skill（例如 `unit-test-remote`、`mcp__bits-ut-remote__run_remote_test`），单测的实际执行与结果校验统一在 `/speckit.verify` 阶段完成。
5.  **实现行为（不在本阶段执行 UT）**:
    -   在每个 subAgent 的 worktree 内，按照 `tasks.md` 与 `plan.md` 完成代码实现，并根据需要补充或完善单元测试文件，使实现保持良好的可测试性。
    -   实施期间不执行统一的 UT 门禁；单测的实际执行与结果校验在后续的 `/speckit.verify` 步骤中集中完成。
    -   **局部自动代码审查（per-worktree）**: 当某个 subAgent 在其 worktree 中完成实现后，必须在该 worktree 下对本次改动涉及的文件调用 code agent 的自动 review 能力，重点检查边界条件、防御性编程、错误处理与异常路径、日志与监控埋点、性能与并发风险以及编码风格；根据 review 结果在本 worktree 内修复问题后，方可将对应任务在 `tasks.md` 中从 `- [ ]` 标记为 `- [x]` 并继续调度下一个任务组。
6.  **集成与冲突处理**:
    -   **合入策略（脚本辅助）**: 在目标开发分支上优先使用 `.specify/scripts/bash/task-merge.sh --target <dev_branch> --source feat/<slug>-task-<ID>` 完成合入；**不要**在 `/speckit.implement_v2` 阶段启用 `--run-local-ut` 或 `--mcp-ut` 选项，单测的执行与质量门禁统一由后续的 `/speckit.verify` 步骤完成。
    -   **提交与推送**: subAgent 在各自的 worktree 分支 (`feat/<slug>-task-<ID>`) 中提交并推送代码。
    -   **MR 策略**:
        -   **策略 A (推荐)**: 各任务分支分别向 `main` 创建独立 MR，便于独立审查。
        -   **策略 B**: 各任务分支合并回基础特性分支（例如 `feat/<slug>`），然后由基础分支统一创建 MR。
    -   **全局自动代码审查（开发分支 / MR 级别）**: 当所有任务分支已经通过 `task-merge.sh` 或等价流程合入目标开发分支，并准备创建或更新 MR 时，应在该开发分支上调用 code agent 的 review 能力，针对本次迭代相对于基线分支（例如 `main`）的整体 diff 进行一次完整代码审查；在进入 `/speckit.verify` 之前，需优先修复其中发现的高优先级问题。
    -   **冲突解决**: 优先使用 `git merge`。若必须变基，请小心操作，**严禁强制推送** (`git push --force`) 到共享分支。
7.  **清理工作**:
    -   **移除 Worktree**: MR 合并后，执行 `git worktree remove .worktrees/<ID>`。
    -   **删除临时分支**: 根据项目策略，可选删除已合并的任务分支 `git branch -d aime/{timestamp}-task-<ID>`。
8.  **进度跟踪与最终校验**:
    -   主 Agent 监控各 subAgent 进度，并在所有并行任务完成后触发 `/speckit.verify` 或等效流程进行统一的质量校验。
    -   自动 review / lint / test 由 Coco Hooks 在 `stop` / `subagent_stop` 事件自动触发；在进入下一任务或后续 verify 阶段之前，Agent 应使用 `files.read` 读取 `.coco/hooks/last_lint_result.json`、`.coco/hooks/last_test_result.json` 和 `.coco/hooks/last_review_summary.txt`，若其中 `status` 显示失败或存在明显问题，应优先修复再继续推进。

## 队列调度与并发循环 (N=3)

-   从 `tasks.md` 中读取所有 `- [ ]` 条目，维护一个 pending 队列，按依赖关系与 `[P]` 并行标记进行分组调度；同一时间最多仅有 3 个 subAgent 并行运行。
-   当任意一个 subAgent 完成其任务组时，主 Agent 必须：
    -   立即在 `tasks.md` 中将对应任务行从 `- [ ]` 改为 `- [x]`，并在行尾追加完成人（@userid）与完成时间（RFC3339）；
    -   重新扫描 pending 队列，从尚未完成的任务组中选择下一个任务组，创建并启动新的 subAgent；
    -   若 pending 队列为空，则结束本轮 `/speckit.implement_v2` 流程。

## 会话长度控制与 Reset 策略

-   **原则**：尽量依赖文件（`spec.md` / `plan.md` / `contracts/` / `data-model.md`、代码与单测文件）而不是长对话历史。主会话主要负责拆分任务与编排流程，subAgent 会话保持“窄上下文”，只携带当前任务组必需的信息。
-   **单任务会话**：当任务本身较复杂或当前会话已经很长时，建议一个 task 使用一个子会话；完成该 task 后，立即 reset 会话，并基于最新的规范与代码文件重新建立上下文，单测执行与验证交由后续的 `/speckit.verify` 步骤统一处理。
-   **多任务并行**：通过 subAgent + 独立 git worktree 分治，每个 subAgent 仅加载本任务组需要的 `spec.md` 片段、`plan.md` 设计、相关 `contracts/` 与 `data-model.md`、以及对应代码/单测文件，避免携带无关历史。
-   **失败重试**：当在最终 `/speckit.verify` 或本地 UT 执行阶段发现单测未通过，或明显感到上下文漂移时，优先更新规划/设计/单测文件，然后在该 subAgent 会话 reset 之后重新执行实现，再通过 `/speckit.verify` 重新校验。
-   **质量门禁**：最终质量判断以代码与 `/speckit.verify` 阶段聚合的 UT 结果为准，不要以对话过程中的表述作为唯一依据。

## 任务配对与 Worktree 示例

### 任务清单 (`tasks.md`)

```markdown
- [ ] T021 [US2] [P] [Test] 为 src/service/order.go 设计用例：创建订单的边界与异常路径
- [ ] T022 [US2] [P] [Impl] 实现创建订单的功能逻辑（与上述单测配套）
- [ ] T035 [US3] [P] [Test] 为 src/handler/user.go 设计用例：用户资料更新接口
- [ ] T036 [US3] [P] [Impl] 实现用户资料更新的功能逻辑（与上述单测配套）
```

### Git Worktree 脚本与命令示例

首先推荐通过脚本完成工作树生命周期，而不是手动输入 git 命令：

-   创建基础分支与任务分支 / worktree: `.specify/scripts/bash/worktree-create.sh`
-   查看当前 worktree 状态: `.specify/scripts/bash/task-status.sh`
-   合并任务分支到开发分支（脚本本身支持在合并后触发本地 UT / MCP UT，但统一的单测门禁应由 `/speckit.verify` 步骤承担）: `.specify/scripts/bash/task-merge.sh`
-   合并完成后清理 worktree 与本地分支: `.specify/scripts/bash/worktree-clean.sh`

在生成的 Agent 命令中，这些脚本会被重写为 `.specify.specify/.specify/scripts/bash/...` 路径，可直接由 `/speckit.implement_v2` 驱动的 Agent 调用；你可以在对话中使用“调用 .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks 所提供的 git helper 脚本执行 worktree 创建/清理/合并”这一类表述，引导 AI 使用脚本而非裸 git 命令。

```bash
# 等效的 git 命令示例（仅供参考）

# 1. 创建基础分支
git checkout -b feat/parallel-impl

# 2. 为用户故事 US2 创建 worktree
git worktree add .worktrees/us2 feat/parallel-impl-task-us2

# 3. 为用户故事 US3 创建 worktree
git worktree add .worktrees/us3 feat/parallel-impl-task-us3

# ...subAgent 在 .worktrees/us2 和 .worktrees/us3 中分别工作...

# 4. 清理 (MR 合并后)
git worktree remove .worktrees/us2
git worktree remove .worktrees/us3
git branch -d feat/parallel-impl-task-us2
git branch -d feat/parallel-impl-task-us3
```


**注意 / 限制**:
- 此命令假定 `tasks.md` 中存在清晰的、可并行执行的任务分组。如果任务依赖复杂，建议使用串行的 `/speckit.implement`。
- Do NOT run unit tests or invoke UT skills (e.g., unit-test-remote) during this command; unit tests are executed only at /speckit.verify.
- 禁止在本命令执行过程中运行单元测试或调用任何 UT 相关 Skill（例如 unit-test-remote、mcp__bits-ut-remote__run_remote_test）；单元测试仅在 /speckit.verify 阶段统一执行。
- 本命令只负责在各个 worktree 中完成代码与（可选）单测文件的编写/更新。
