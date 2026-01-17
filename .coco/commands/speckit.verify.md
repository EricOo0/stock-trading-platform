---
description: 统一执行最终质量校验（UT、MCP UT、lint、静态规则、任务对齐）。
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json --include-tasks
  verify_local_ut_sh: .specify/scripts/bash/verify-local-ut.sh
  verify_mcp_ut_sh: .specify/scripts/bash/verify-mcp-ut.sh
  verify_static_sh: .specify/scripts/bash/verify-static.sh
  verify_tasks_align_sh: .specify/scripts/bash/verify-tasks-align.sh
---

## 用户输入

```text
$ARGUMENTS
```

## 概述

使用本命令在实现完成后统一执行最终质量校验，聚合本地 UT、MCP UT、静态规则以及 `tasks.md` 与代码/单测的对齐情况，形成一个可用于 MR 前置 gate 或主分支合并 gate 的“总闸门”。

### 步骤

1.  **Hooks 结果回顾**：如果存在 `.coco/hooks/last_lint_result.json`、`.coco/hooks/last_test_result.json` 或 `.coco/hooks/last_review_summary.txt`，Agent 应使用 `files.read` 读取并总结其中的状态与错误信息，将其视作用户反馈的一部分；如发现 lint / test / review 失败，应优先修复相关问题，再继续后续 gate。
2.  **环境检查**：调用 `.specify/scripts/bash/check-prerequisites.sh --json --include-tasks`，输出 `FEATURE_DIR` 与 `AVAILABLE_DOCS`；加载 `plan.md` / `spec.md` / `tasks.md` 等核心设计与任务文件，确认当前特性下的实现上下文完整。
3.  **本地 UT**：调用 `{verify_local_ut_sh}`，优先从环境变量 `SPEC_KIT_LOCAL_UT_CMD` 读取本地单测命令（例如 `pytest` 或 `go test ./...`）；若未配置，则脚本默认执行 `go test ./...`。命令通过 `bash -lc` 运行，退出码非 0 时视为本地 UT 失败，并将错误信息纳入最终报告。
4.  **MCP UT**：调用 `{verify_mcp_ut_sh}`，从环境变量 `SPEC_KIT_MCP_UT_CMD` 读取 UT MCP gate 命令，并要求最终 `exit_code == 0` 才算通过；若未配置该环境变量，则视为“可选 gate 未开启”，脚本打印提示并退出 0。脚本会解析输出以检测已知参数错误（如 “test_kind 为 package 时，必须提供 test_func 或 test_suite 参数” 或 “package 需 suite/func”），在命中该类错误时，通过 `SPEC_KIT_MCP_UT_FALLBACK_CMD` 触发一次降级到 directory 模式的重试。在执行 MCP UT 时，Agent 应优先使用 unit-test-remote Skill 来封装与解析测试结果（仅在 verify 阶段）。
5.  **静态 & lint & 编译检查**：调用 `{verify_static_sh}`，基于当前仓库的语言栈自动执行静态 / lint / 编译 gate：
    -   若存在 `package.json`，按 `pnpm` → `yarn` → `npm` 的优先级检测可用的包管理器，并依次运行 `lint` 与 `build`（例如 `pnpm lint` + `pnpm build` / `yarn lint` + `yarn build` / `npm run lint` + `npm run build`）；任一命令退出码非 0 即视为本 gate 失败。
    -   若存在 `go.mod`，运行 `go build ./...` 与 `go vet ./...`，任一失败即视为本 gate 不通过。
    -   若仓库中存在被 git 跟踪的 `.py` 文件，则使用 `python3 -m py_compile` 对所有 Python 文件做语法检查；若本地安装了 `ruff` 或 `flake8`，还会运行相应的静态检查（若均不存在则跳过并打印 INFO）；只要其中一步失败，脚本就以非 0 状态退出。
    -   当以上语言栈均未命中时，脚本仅打印“无适用静态检查，跳过”并以 0 退出。
    该脚本退出非 0 时视为“静态 / lint / 编译 gate 未通过”，应在修复后重跑本命令。
6.  **任务对齐**：调用 `{verify_tasks_align_sh}`，读取 `tasks.md`，对其中包含 `[Test]` / `[Impl]` 的任务条目进行简单对齐检查：从任务描述中提取包含 `/` 的路径片段（如 `src/service/order.go`、`tests/service/order_test.go`），验证这些路径在当前特性目录下是否存在；收集所有缺失路径并输出清单——这既是 `tasks.md` 与代码/单测文件的一致性检查，也可作为“单测编写是否覆盖需求路径”的代理指标；若存在缺失则以非零状态退出。
7.  **汇总与出结论**：综合上述各脚本的退出状态与输出日志：若全部步骤成功（退出码为 0），则给出“验证通过”的结论；否则输出失败清单（例如本地 UT/MCP UT 失败、任务对齐缺失文件等），并给出明确的修复建议路径（补齐或修正单测、修复实现代码、完善静态检查或任务条目后重跑本命令）。

## 注意事项

- 禁止在 verify 流程中建议或自动执行 `git push --force`；所有 git 操作应遵循安全分支策略，优先使用 merge，避免破坏共享分支历史。
- 推荐将 `/speckit.verify` 作为 Merge Request 前置 gate 或主分支合并前的统一质量闸门：通常在完成 `/speckit.implement` 或 `/speckit.implement_v2` 后，由 AI 或开发者主动运行一次，确保 UT（本地 + MCP）、静态规则与 `tasks.md` 对齐全部通过后再发起或合入 MR。
