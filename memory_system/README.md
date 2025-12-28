# 🧠 独立三层记忆系统 (Triple-Layer Memory System)

这是一个独立部署的认知微服务，模拟人类大脑的记忆分层与进化机制，为外部系统提供具备人格化特征、时效感知和逻辑自省能力的记忆存储方案。

---

## 🏗️ 系统架构 (Architecture)

系统采用三层隔离存储架构，实现信息从“原始素材”到“人格抽象”的演进：

1.  **短期记忆 (STM - Working Memory)**
    *   **定位**: 相当于 CPU 高速缓存。
    *   **载体**: 内存 `deque` + 本地 `JSON` 持久化。
    *   **内容**: 最近的原始会话语料、实时上下文、未结算的思考过程。
    *   **策略**: 默认保留最近 5-10 轮对话，超过 Token 限制时由 `manager` 触发压缩。

2.  **中期记忆 (MTM - Episodic Memory)**
    *   **定位**: 相当于 内存/硬盘。
    *   **载体**: `ChromaDB` (向量) + `NetworkX` (知识图谱)。
    *   **内容**: 结构化事件、投资见解 (`InvestmentInsight`)、金融事实。
    *   **策略**: 支持语义搜索、**图谱联想扩展**以及**时间衰减算法**（Temporal Decay）。

3.  **长期记忆 (LTM - Semantic Memory)**
    *   **定位**: 相当于 人格核心/元认知。
    *   **载体**: `JSON` (本地持久化) + `ChromaDB` (向量经验)。
    *   **内容**: **用户画像 (User Persona)**、投资原则、核心价值观、通用经验法则。
    *   **策略**: 通过对 MTM 进行聚类分析和 LLM 总结蒸馏产生，具有最高的稳定性和指导意义。

---

## 🔄 数据流 (Data Flow)

记忆系统中的信息流转遵循以下三个核心过程：

### 1. 采集流 (Ingestion Pipeline)
用户/Agent 的对话通过 `/add` 接口实时进入 **STM**。系统会自动根据 Token 预算管理近期上下文，确保 STM 始终保持在热状态且不溢出。

### 2. 检索流 (Retrieval Pipeline)
调用 `/context` 时，系统执行“记忆检索增强” (RAG+)：
- **实体提取**: 从 Query 中提取股票代码或金融概念。
- **多层检索**: 同步从 STM、LTM（用户画像/原则）和 MTM（向量检索+图谱扩展）中获取数据。
- **冲突检测**: 自动检查历史记忆中的观点一致性（例如：用户曾看多 NVDA 但现在看空，系统将注入 `[Memory Reflection]`）。
- **重排序**: 应用时间衰减函数，确保新鲜资讯权重更高。

### 3. 进化流 (Evolution Pipeline)
这是一个异步沉淀过程，由 `/finalize` 触发：
- **蒸馏**: 将 STM 中的原始文本提炼为结构化的 Episodic Events。
- **画像更新**: 基于新增会话增量更新 LTM 中的用户投资风格、风险偏好等画像。
- **聚类与抽象**: 定期将大量 MTM 条目聚类，抽象为通用的长期经验法则。

---

## 📡 暴露接口 (API Reference)

服务默认监听 `10000` 端口，基础路径为 `/api/v1`：

| 接口 | 方法 | 功能描述 | 关键参数 |
| :--- | :--- | :--- | :--- |
| `/memory/add` | `POST` | 实时同步语料至 STM | `user_id`, `agent_id`, `content`, `metadata` |
| `/memory/context` | `POST` | 获取增强后的复合上下文 | `user_id`, `agent_id`, `query`, `session_id` |
| `/memory/finalize` | `POST` | 异步启动记忆结算（STM -> MTM/LTM） | `user_id`, `agent_id` |
| `/memory/task/{id}`| `GET` | 查询异步结算任务状态 | `task_id` |
| `/memory/stats` | `GET` | 获取存储统计与画像摘要 | `user_id`, `agent_id` |

---

## 🚀 快速上手 (Usage)

### 1. 启动服务
确保已安装 `requirements.txt` 依赖，在 `memory_system` 目录下运行：
```bash
python -m api.server
```

### 2. 核心配置
编辑 `memory_system/.config.yaml` (参考 `example.config.yaml`)：
- **LLM**: 配置 API Key 和 Base URL 用于记忆蒸馏和自省。
- **Chroma**: 设置向量数据库存储路径。
- **Decay**: 调整时间衰减常数以控制记忆淡忘速度。

### 3. 客户端集成 (Python)
使用内置 `MemoryClient` 实现无感集成：
```python
from backend.infrastructure.adk.core.memory_client import MemoryClient

# 1. 初始化
client = MemoryClient(user_id="user_001", agent_id="researcher")

# 2. 会话中：添加语料
client.add_memory("关注特斯拉最近的自动驾驶进展", role="user")

# 3. 决策前：获取上下文
context = client.get_context("分析 TSLA")
# context 包含: persona, principles, stm, mtm, reflection...

# 4. 结束后：启动结算（异步）
client.finalize()
```

---

## 🛡️ 核心特性 (Features)

- **冲突自省 (Reflection)**: 系统会自动识别记忆中的观点反转，提示 LLM 关注用户的思维转变。
- **跨会话连贯性**: 会话结算后，STM 默认保留最近 5 轮数据，为下一次新会话提供“热启动”背景。
- **时间重排**: 采用 $Score = Sim \times \frac{1}{1 + \ln(1 + \Delta days)}$ 算法平衡语义相关性与时效性。
- **Token 精确管控**: 基于 `tiktoken` 实现 STM > Persona > MTM > Principles 的动态截断优先级。

---
**最近更新**: 2025-12-27 (v1.7 完善架构说明、数据流定义及 API 文档)
