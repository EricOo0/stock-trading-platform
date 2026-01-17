# Golang Mockery 生成技能（参考文档）

## 1. 概述

本技能旨在统一 Golang 项目中的 Mock 代码生成方式，确保所有 Mock 文件均通过 `mockery` 工具结合 `go:generate` 命令生成。

**核心目标**：
- **禁止手写 Mock**：在任何生产或测试代码中，不允许出现手写的 Mock 结构体。
- **标准化生成命令**：所有 Mock 文件必须通过 `mockery` 生成，并启用 `--with-expecter=true` 选项，以便在测试中获得更流畅的链式调用体验。
- **自动化集成**：为 `speckit.implement` 等上层 Agent 提供标准化的调用接口，使其能够在实现和测试阶段自动完成 Mock 相关代码的维护。

---

## 2. 触发条件

当 Agent（如 `speckit.implement` 或 `Coco`）在执行代码实现或编写单元测试任务时，识别到需要为某个 Golang 接口创建 Mock 实现时，应触发本技能。

**示例场景**：
- 为一个新的 Service 实现编写单元测试，需要 Mock 其依赖的 Repository 接口。
- 修改一个已有的业务逻辑，该逻辑依赖一个新的外部接口，需要在测试中 Mock 这个新接口。
- **示例接口**：`IPackAuthAccountRepo`

---

## 3. 输入参数

本技能接受以下参数，以支持灵活的 Mock 生成策略。

| 参数名 | 类型 | 是否可选 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `interface_names` | `List<String>` | 可选 | (空列表) | 需要生成 Mock 的接口名称列表。如果为空，技能将自动扫描指定包路径下的所有接口。 |
| `package_root` | `String` | 必选 | (无) | 项目的根包路径，例如 `code.byted.org/bitable/backend-core`。用于定位接口定义和生成 Mock 文件。 |
| `mock_target_path_rule` | `String` | 必选 | (无) | Mock 文件生成的目标路径规则。Agent 应遵循仓库的目录与包名约定来设定此值。 |

---

## 4. 行为流程

本技能被触发后，将严格按照以下步骤执行，以确保 Mock 代码的一致性和可维护性。

### 4.1 扫描与注释注入

1. **扫描接口定义**：
   - 技能首先在指定的 `package_root` 和 `mock_target_path_rule` 范围内，根据 `interface_names` 或自动发现的策略，定位到需要 Mock 的接口定义文件（例如 `repo.go`）。

2. **检查与插入 `go:generate` 注释**：
   - 对于每一个目标接口（如 `IPackAuthAccountRepo`），检查其定义上方是否已存在 `//go:generate mockery` 注释。
   - **如果缺失**，技能必须在该接口定义的正上方插入一行 `go:generate` 注释。注释的格式是固定的：
     ```go
     //go:generate mockery --name=<InterfaceName> --with-expecter=true
     ```
     **示例**：
     ```go
     //go:generate mockery --name=IPackAuthAccountRepo --with-expecter=true
     type IPackAuthAccountRepo interface {
         // ...
     }
     ```
   - **如果已存在**，则不做任何操作，以避免重复或冲突。

### 4.2 输出执行指令

- 技能在完成 `go:generate` 注释的检查与注入后，**不会直接执行代码生成**。
- 相反，它会向用户或上层 Agent **输出** 需要在终端中执行的命令，以完成 Mock 文件的生成或更新：
  ```bash
  go generate ./...
  ```
- 这个指令应在 Agent 的最终输出或交互提示中清晰地展示给开发者。

### 4.3 生成/更新测试用例中的引用

- 技能在生成或修改单元测试文件时，**必须假设 `go generate ./...` 已经被执行**。
- **禁止在测试代码中手写 Mock 实现**：严禁在测试文件（`_test.go`）中定义任何临时的 `struct` 来实现被 Mock 的接口。
- **使用 `mockery` 产物**：测试代码必须 `import` 由 `mockery` 生成的 Mock 包，并使用其提供的 `New...` 函数来创建 Mock 实例。

  **示例**：在测试用例中引用并使用 `mockery` 生成的 Mock：
  ```go
  package usecase_test

  import (
      "testing"
      "github.com/stretchr/testify/assert"
      "github.com/stretchr/testify/mock"

      // 1. 导入 mockery 生成的 mock 包
      "code.byted.org/bitable/backend-core/domain/dmservice/mocks"
  )

  func TestMyService_DoSomething(t *testing.T) {
      // 2. 使用 New... 函数创建 Mock 实例
      mockRepo := mocks.NewIPackAuthAccountRepo(t)

      // 3. 使用 expecter 配置 Mock 行为与返回值
      mockRepo.EXPECT().
          GetAccount(mock.Anything, "user123").
          Return(&domain.Account{ID: "user123"}, nil)

      // 注入 mockRepo 并执行被测逻辑...
      myService := usecase.NewMyService(mockRepo)
      account, err := myService.DoSomething(context.Background(), "user123")

      // 断言
      assert.NoError(t, err)
      assert.NotNil(t, account)
      mockRepo.AssertExpectations(t)
  }
  ```

---

## 5. 集成指引

为了确保本技能在不同的 Agent 工作流中被正确、一致地调用，请遵循以下集成约定。

### 5.1 `speckit.implement` 模板调用约定

- 在 `speckit.implement` 的模板（例如 `templates/commands/implement.md`）中，必须明确启用本技能。
- 在与测试相关的章节，应包含如下指令：

  > **测试与 Mock 约束 (Golang)**
  >
  > 在为本次改动编写或更新单元测试时，必须启用 `mockery-generate` Skill 来处理所有接口的 Mock 生成。
  > 1.  **禁止手写 Mock**：不得在任何代码中手写 Mock 结构体。
  > 2.  **依赖 `go:generate`**：Agent 应检查并为需要 Mock 的接口（如 `IPackAuthAccountRepo`）添加 `//go:generate mockery --name=... --with-expecter=true` 注释。
  > 3.  **提示用户执行命令**：在任务完成的总结说明中，必须提示用户在本地执行 `go generate ./...` 以更新 Mock 文件。
  > 4.  **使用 `mockery` 产物**：测试代码应直接 `import` 并使用 `mockery` 生成的包，如示例所示。

### 5.2 Coco/Agent 提示词嵌入示例

在指导 Coco 或其他 Agent 执行实现或测试任务时，可以在提示词中直接嵌入对本技能的调用要求。

**示例提示词**：

> “请为 `PackAuthService` 实现 `GetAccount` 方法，并为其编写单元测试。在测试中，你需要 Mock `IPackAuthAccountRepo` 接口。
>
> **Mock 要求**：
> - **启用 `mockery-generate` Skill**。
> - 在 `IPackAuthAccountRepo` 接口定义处添加 `go:generate mockery` 注释。
> - 在测试代码中，使用 `mockery` 生成的 Mock 对象，并利用 `expecter` 设置调用预期。
> - 最后在说明中提示我需要执行 `go generate`。”

---

## 6. 目录与包名建议

合理的目录结构是避免循环依赖和维护清晰性的关键。

- **`mocks` 包位置**：
  - `mockery` 生成的 Mock 文件应统一放置在被 Mock 接口所在包的子目录 `mocks` 中。
  - 例如，如果接口定义在 `domain/dmservice/`，则其 Mock 文件应生成在 `domain/dmservice/mocks/`。
    ```
    domain/
    └── dmservice/
        ├── pack_auth.go         // 包含 IPackAuthAccountRepo 接口定义
        └── mocks/
            └── IPackAuthAccountRepo.go  // mockery 生成的 Mock 文件
    ```

- **生成文件路径约定**：
  - `mockery` 通常会自动在指定的输出目录下生成与接口名对应的文件（如 `IPackAuthAccountRepo.go`）。
  - 应避免将多个无关领域的 Mock 文件混杂在同一个 `mocks` 目录中，以防止包名冲突和依赖混乱。如果 `dmservice` 下有多个子域，可以考虑在 `dmservice/subdomain/mocks` 中生成。

- **避免循环依赖**：
  - 将 Mock 文件放在接口包的子目录中，可以有效避免因测试代码 `import` Mock 包，而 Mock 包又需要 `import` 接口包（如果分开存放）可能导致的循环依赖问题。

---

## 7. 失败回退

在某些特殊情况下，例如目标仓库的 CI/CD 流程或基建环境 **不允许** 使用 `go:generate`，技能应采取以下回退策略。

1.  **不插入 `go:generate` 注释**：
    - 技能在检测到 `go:generate` 被禁用的环境后，应跳过“行为流程”中的 4.1 步骤，即不向任何接口文件添加 `go:generate mockery` 注释。

2.  **生成 `mock-generate-list.md` 清单文件**：
    - 在项目的根目录或 `.specify/` 目录下，生成一个名为 `mock-generate-list.md` 的 Markdown 文件。
    - 该文件应包含一个清晰的清单，列出所有需要手动生成 Mock 的接口和对应的 `mockery` 命令。

    **`mock-generate-list.md` 文件内容示例**：
    ```markdown
    # Mockery 生成清单

    本仓库环境禁用了 `go:generate`。请根据以下清单手动执行 `mockery` 命令以生成或更新 Mock 文件。

    ## 待处理接口

    | 接口 | 所在文件 | 推荐 `mockery` 命令 |
    | --- | --- | --- |
    | `IPackAuthAccountRepo` | `domain/dmservice/pack_auth.go` | `mockery --name=IPackAuthAccountRepo --with-expecter=true --inpackage --case=underscore` |
    | `INewOtherInterface` | `infra/rpcclient/other.go` | `mockery --name=INewOtherInterface --with-expecter=true --inpackage --case=underscore` |

    ---
    *该文件由 `mockery-generate` Skill 自动生成。*
    ```

3.  **在 README 中提示**：
    - 同时，技能应向项目的 `README.md` 或相关开发文档中追加一个提示片段，告知开发者如何使用这份清单。

    **README 提示示例**：
    ```markdown
    ## Mock 代码生成
    本仓库的 Mock 文件通过 `mockery` 手动生成。请在修改或新增接口后，参考 [`mock-generate-list.md`](./mock-generate-list.md) 文件中的命令，手动更新 Mock 代码。
    ```

---

## 8. 限制与注意事项

- **避免手写 Stub**：除了禁止手写完整的 Mock 结构体外，也应避免在测试中为了满足接口而手写临时的、功能不全的伪实现（Stub）。所有测试替身都应通过 `mockery` 生成。
- **与 `gomock`/`ginkgo` 并存策略**：
  - `mockery` 专注于从接口生成 Mock 代码。
  - `gomock` 则是在测试运行时用于控制 Mock 对象行为（如设置期望、断言调用）的框架。两者需要配合使用。
  - 在使用 `ginkgo`/`gomega` 作为测试框架的项目中，`mockery` 的产物同样兼容，可以无缝集成。
- **CI 对 SatCheck 不新增 Error 的要求**：
  - `mockery` 生成的代码本身是符合 Go 语言规范的。
  - 在引入或更新 Mock 文件后，必须确保 CI 中的静态分析（SatCheck）流程 **不会因此新增 Error 级别的问题**。通常 `mockery` 生成的代码质量较高，但如果项目有特殊的 lint 规则，需要关注其兼容性。

---

## 9. 示例片段

为了更直观地展示技能的核心操作，以下提供了两个关键场景的最小化代码示例。

### 9.1 为 `IPackAuthAccountRepo` 添加 `go:generate` 注释

**文件**: `domain/dmservice/pack_auth.go`

```go
package dmservice

import "context"

// ... 其他 import ...

// highlight-start
//go:generate mockery --name=IPackAuthAccountRepo --with-expecter=true
// highlight-end
type IPackAuthAccountRepo interface {
    GetAccount(ctx context.Context, userID string) (*Account, error)
    SaveAccount(ctx context.Context, account *Account) error
}

type Account struct {
    // ...
}
```
*技能执行后，会在 `IPackAuthAccountRepo` 接口定义上方，确保存在 `//go:generate mockery ...` 这一行。*

### 9.2 测试中引用 Mock 的最小样例

**文件**: `domain/dmservice/pack_auth_test.go`

```go
package dmservice_test

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"

    // 假设 mockery 生成的 mock 包路径如下
    "code.byted.org/bitable/backend-core/domain/dmservice/mocks"
    "code.byted.org/bitable/backend-core/domain/dmservice"
)

func TestPackAuthService_Authenticate(t *testing.T) {
    // 1. 创建 Mock 实例
    mockRepo := mocks.NewIPackAuthAccountRepo(t)
    
    // 2. 实例化被测服务，并注入 Mock 依赖
    authService := dmservice.NewPackAuthService(mockRepo)
    
    // 3. 设置 Mock 对象的期望行为
    // 期望：当调用 GetAccount，输入任意 context 和 "existing_user" 时，
    // 返回一个指定的 Account 实例和 nil 错误。
    expectedAccount := &dmservice.Account{ID: "existing_user", Name: "test"}
    mockRepo.EXPECT().
        GetAccount(mock.Anything, "existing_user").
        Return(expectedAccount, nil).
        Once() // 期望该调用只发生一次

    // 4. 执行被测函数
    result, err := authService.Authenticate(context.Background(), "existing_user")

    // 5. 断言结果
    assert.NoError(t, err)
    assert.Equal(t, expectedAccount, result)

    // 6. 验证所有在 EXPECT() 中设置的期望是否都已满足
    mockRepo.AssertExpectations(t)
}
```
*该测试样例展示了如何正确地导入和使用由 `mockery` 生成的 Mock 对象，包括创建实例、设置期望和最终验证。*
