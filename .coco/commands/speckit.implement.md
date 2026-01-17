---
description: 通过处理和执行 tasks.md 中定义的所有任务来执行实现计划。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

1.  **运行 `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`** 并解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS`。
2.  **加载和分析实现上下文**:
    -   **必需**: `tasks.md` (完整的任务列表)。
    -   **必需**: `plan.md` (技术栈、架构)。
    -   **可选**: `data-model.md`, `contracts/`, `research.md`。
3.  **验证项目设置**:
    -   创建或验证 `.gitignore` 等忽略文件。
4.  **解析 `tasks.md`** 结构并提取：
    -   任务阶段、依赖关系、任务详情、执行流程。
5.  **按任务计划执行实现**:
    -   **分阶段执行**: 在进入下一阶段之前完成每个阶段。
    -   **尊重依赖关系**: 按顺序运行串行任务，并行任务 `[P]` 可一起运行。
    -   **单元测试友好实现**: 实现阶段可以完善测试代码，但不在本命令统一触发 UT；UT 统一在 /speckit.verify。
6.  **进度跟踪和错误处理**:
    -   在每个已完成的任务后报告进度。
    -   如果任何非并行任务失败，则停止执行。
    -   每完成一个任务必须立刻在 `tasks.md` 将该行从 `- [ ]` 改为 `- [x]`，并在该行末尾追加完成人（@userid）与完成时间（RFC3339）。使用 `files.read` / `files.write_file` 完成写回。
    -   在进入下一任务前，执行一次 pending 任务扫描（`- [ ]` 条目），并按依赖与并行标记选择下一个任务；若无 pending，则结束。
7.  **完成验证**:
    -   验证所有必需的任务是否已完成。
    -   检查实现的功能是否与原始规格书匹配。

**注意**: 此命令假定 `tasks.md` 中存在完整的任务分解。如果任务不完整或缺失，建议首先运行 `/speckit.tasks` 重新生成任务列表。

## 技能使用策略（Coco Skills）

### mockery-generate

-   如需为 Go 接口生成 mock，请使用 mockery + go:generate；单测执行与验证在最终 `/speckit.verify` 阶段完成。
- **触发规则**：当满足以下任一条件时，必须启用 `mockery-generate` Skill：
  - 当前实现语言为 Go，且本次改动涉及单测、接口桩或 Mock；
  - 上下文（spec、plan、tasks、代码路径等）中出现以下任意关键词：`mock`、`mockery`、`go:generate`、`Expecter`、`I*Repo`（接口名包含 `Repo`）。
- **启用 Skill 后的操作要求**：
  - 在需要生成 Mock 的接口定义处，插入或校验以下注释（按实际接口名替换 `<Interface>`）：
    ```go
    //go:generate mockery --name=<Interface> --with-expecter=true
    type <Interface> interface {
        // ...
    }
    ```
  - 在实现说明或任务总结中，显式提示开发者在本地执行：
    ```bash
    go generate ./...
    ```
    以生成或更新 Mock 代码。
  - 在 Go 单测中，只引用 mockery 生成的 Mock 类型，**禁止**手写实现接口的 mock struct。
- **不允许 `go:generate` 的回退策略**：
  - 若仓库规范不允许提交 `//go:generate` 注释或执行 `go generate`：
    - 生成 `mock-generate-list.md` 清单文件，列出需要生成 Mock 的接口名、所在包路径及推荐的 mockery 命令；
    - 在 README 或变更说明中提示人工在本地按清单执行 mockery 命令。
- **简短示例**：
  ```go
  // 在接口定义处：
  //go:generate mockery --name=IPackAuthAccountRepo --with-expecter=true
  type IPackAuthAccountRepo interface {
      // ...
  }
  ```
  ```go
  // 在单测中使用 expecter：
  func TestFoo(t *testing.T) {
      repo := mockrepo.NewIPackAuthAccountRepo(t)
      repo.EXPECT().GetAccount(ctx, "uid-xxx").Return(&Account{}, nil)

      // 调用被测逻辑并断言
  }
  ```

