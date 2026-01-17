# 远程单元测试 Skill (unit-test-remote) - 参考文档

## 1. 概述

本 Skill 的核心是提供一个稳定、可预测的接口，用于在 `speckit.implement` 流程中执行远程单元测试。它将不稳定的、依赖复杂环境的 `bits-ut` 命令封装成一个确定性的 MCP 工具，是实现 TDD（测试驱动开发）闭环的关键。

**目标**：确保所有代码变更在最终确认前，都经过了单元测试的严格验证，并将测试失败的排查成本降至最低。

---

## 2. 输入参数详解

本 Skill 底层调用的是 `bits-ut-remote` MCP，其 `run_remote_test` 工具接受以下参数。调用方（如 `speckit.implement`）必须正确提供这些参数。

| 参数名 | 类型 | 是否可选 | 描述 |
| :--- | :--- | :--- | :--- |
| `working_directory` | `String` | 必选 | 实际执行测试的工作目录。**通常是测试文件所在包的绝对路径**，例如 `/path/to/repo/service/user`。 |
| `working_package` | `String` | 必选 | Git 仓库的根目录，即包含 `.codebase` 目录的上级目录。例如 `/path/to/repo`。 |
| `test_kind` | `String` | 可选 | 测试范围类型，默认为 `package`。可选值：<br>- `file`：按文件运行，此时 `files` 参数必填。<br>- `directory`：按目录运行，此时 `directory` 参数必填。<br>- `package`：按 Go 包路径和名称匹配运行，此时 `package_path` 和 `test_func`/`test_suite` 必填。 |
| `package_path` | `String` | `test_kind` 为 `package` 时必选 | 测试文件的 Go 包路径，例如 `code.byted.org/larkmail/migration-admin/database`。 |
| `files` | `String` | `test_kind` 为 `file` 时必选 | 要运行的测试文件的路径，相对于 `working_package`。 |
| `directory` | `String` | `test_kind` 为 `directory` 时必选 | 要运行的测试目录的路径，相对于 `working_package`。 |
| `test_func` | `String` | 可选 | 要运行的测试函数名，例如 `TestCreateUser`。 |
| `test_suite` | `String` | 可选 | 要运行的测试套件名，例如 `UserTestSuite`。`test_func` 和 `test_suite` 至少提供一个。 |
| `pipeline_file` | `String` | 可选 | CI 的 YAML 配置文件路径，默认为 `./.codebase/pipelines/ci.yaml`。如果子目录有独立配置（如 `ci-sub.yaml`），需要显式指定。 |

---

## 3. 工作流与 TDD 集成

`unit-test-remote` Skill 是 `implement` 命令模板中 TDD 流程的核心环节。

### 3.1 `implement` 命令中的 TDD 流程

1.  **编写或更新测试**：在修改或新增业务逻辑之前，首先编写一个或多个 **将会失败** 的单元测试。
2.  **编写业务逻辑**：根据需求和设计，实现业务逻辑，目标是让之前失败的测试变为通过。
3.  **运行单元测试（调用本 Skill）**：
    -   在代码实现完成后，`implement` 命令 **必须** 调用 `unit-test-remote` Skill。
    -   Agent 需要根据上下文，正确组装 `run_remote_test` 所需的参数。
4.  **检查结果并迭代**：
    -   如果返回的 `exit_code` 是 `0`，则认为当前任务的实现已通过验证，可以继续下一个任务。
    -   如果 `exit_code` 非 `0`，则 **实现失败**。Agent 必须：
        -   **解析失败日志**：从返回的 `output` 字段中提取失败的测试用例名称、代码位置和错误信息。
        -   **重新进入修复循环**：基于失败日志，重新分析、修改代码，然后再次调用本 Skill，直到所有测试通过。
5.  **完成任务**：只有当所有相关单元测试都通过（`exit_code == 0`）时，`implement` 中的一个任务才算真正完成。

### 3.2 Agent 调用示例

在 `implement` 流程的最后，Agent 应生成类似以下的思考与调用过程：

> **思考**: 代码和测试已生成。现在进入 TDD 验证阶段，我需要调用 `unit-test-remote` Skill 来运行刚刚为 `TestCreateUser_Success` 编写的测试。
>
> - **`working_directory`**: `/Users/bytedance/workspace/larkmail/user-center/service`
> - **`working_package`**: `/Users/bytedance/workspace/larkmail/user-center`
> - **`test_kind`**: `package`
> - **`package_path`**: `code.byted.org/larkmail/user-center/service`
> - **`test_func`**: `TestCreateUser_Success`
>
> 我将调用 `run_remote_test` 工具并检查 `exit_code`。
>
> ```json
> {
>   "tool": "run_remote_test",
>   "arguments": {
>     "working_directory": "/Users/bytedance/workspace/larkmail/user-center/service",
>     "working_package": "/Users/bytedance/workspace/larkmail/user-center",
>     "test_kind": "package",
>     "package_path": "code.byted.org/larkmail/user-center/service",
>     "test_func": "TestCreateUser_Success"
>   }
> }
> ```

---

## 4. 最佳实践与注意事项

-   **明确测试范围**：
    -   为了提高效率，调用时应尽可能精确地指定测试范围。优先使用 `test_func` 或 `test_suite`。
    -   当需要验证整个包或整个目录的测试时，再使用 `directory` 或 `package`（不带 `test_func`）模式。
-   **处理 `pipeline_file` 路径**：
    -   大多数仓库的 CI 配置文件位于根目录的 `.codebase/pipelines/ci.yaml`。
    -   但部分大型单体仓库可能在子目录（如 `service/user/.codebase/pipelines/ci-user.yaml`）中存放独立的配置文件。Agent 在调用时需要能够根据上下文识别并传入正确的 `pipeline_file` 路径。
-   **日志解读**：
    -   本 Skill 返回的 `output` 是经过提炼的摘要。如果需要排查复杂问题，可以引导用户查看 `test_logs/latest.log` 中的完整原始日志。
-   **与 `mockery-generate` Skill 的协同**：
    -   `unit-test-remote` 通常在 `mockery-generate` Skill 执行之后被调用。
    -   `mockery-generate` 负责确保 Mock 代码是最新的，而 `unit-test-remote` 则使用这些 Mock 代码来验证业务逻辑的正确性。两者共同构成了完整的“编码-测试”闭环。
