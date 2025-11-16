# Implementation Plan: 行情数据获取工具

**Branch**: `001-market-data-tool` | **Date**: 2025-11-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-market-data-tool/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

实现一个基于Claude Skill的免费行情数据获取工具，支持A股、美股、港股的实时股票行情数据获取。采用Yahoo Finance作为主数据源，新浪财经作为备用数据源，通过Python函数接口集成到Claude，提供中文优先的用户体验。工具支持单只股票和批量查询，内置限流和熔断机制，确保在非高频交易场景下的稳定运行。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+
**Primary Dependencies**: yfinance>=0.2.33, pandas>=1.5.0, requests>=2.28.0, python-dotenv>=0.19.0
**Storage**: N/A (无本地存储，直接从API获取数据)
**Testing**: pytest + pytest-mock
**Target Platform**: Linux/Windows/macOS (支持Claude Skill运行的环境)
**Project Type**: single (Claude Skill)
**Performance Goals**: 单只股票查询响应时间<5秒，支持100+股票代码，95%+数据准确性
**Constraints**: 非高频交易用途，数据延迟≤60分钟，A股限流120次/h，美股港股限流60次/h
**Scale/Scope**: 免费API限流范围内个人用户投资决策支持

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. 中文优先原则 ✅
- **Status**: COMPLIANT - All documentation in Chinese, Chinese error messages
- **Evidence**: Chinese-first design in spec.md, Chinese error messages in data-model.md
- **Verification**: API responses include Chinese stock names and error messages

### II. Claude Skill集成原则 ✅
- **Status**: COMPLIANT - Standard Skill folder structure with main_handle() interface
- **Evidence**: `main_handle(text_input)` function defined in research.md, skill.md description file
- **Verification**: Text protocol processing for natural language queries

### III. 投资数据安全原则 ✅
- **Status**: COMPLIANT - No sensitive data storage, API-only data access
- **Evidence**: Storage: N/A, no credentials stored, rate limiting implemented
- **Verification**: All data fetched fresh from APIs, no local persistence

### IV. AI决策透明原则 ✅
- **Status**: COMPLIANT - Clear data source attribution, error transparency
- **Evidence**: `data_source` field in responses, detailed error codes and suggestions
- **Verification**: Circuit breaker pattern provides service status transparency

### V. 实时更新原则 ✅
- **Status**: COMPLIANT - Real-time API data fetching, no caching by default
- **Evidence**: Current timestamp in every response, no storage layer
- **Verification**: Live API calls on each request, timestamp validation

### VI. 测试驱动开发原则 ✅
- **Status**: COMPLIANT - pytest framework specified, test-first approach
- **Evidence**: pytest + pytest-mock in testing requirements, validation functions defined
- **Verification**: Comprehensive validation functions in data-model.md

### VII. 用户体验优先原则 ✅
- **Status**: COMPLIANT - Chinese-first interface, simplified operations
- **Evidence**: Natural language processing, multiple market support, error suggestions
- **Verification**: Text protocol allows Chinese natural language queries

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# Single Claude Skill project
skills/market_data_tool/
├── __init__.py
├── skill.py              # 主要技能实现
├── skill.md             # Claude Skill描述文件
├── requirements.txt     # 依赖包
├── config.py            # 配置文件
├── data_sources/        # 数据源模块
│   ├── __init__.py
│   ├── yahoo_finance.py # Yahoo Finance接口
│   └── sina_finance.py  # 新浪财经备用接口
├── models/              # 数据模型
│   ├── __init__.py
│   └── schemas.py       # 数据结构定义
├── utils/               # 工具函数
│   ├── __init__.py
│   ├── validators.py    # 数据验证
│   └── error_handler.py # 错误处理
└── tests/               # 测试文件
    ├── __init__.py
    ├── test_skill.py    # 技能测试
    ├── test_data_sources/ # 数据源测试
    └── test_validators.py # 验证函数测试
```

**Structure Decision**: 选择Option 1 - Single Claude Skill项目结构。该设计符合宪法原则的Claude Skill集成要求，模块化设计便于维护和测试，支持自然语言文本协议处理。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
