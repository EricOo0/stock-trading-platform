# Multi-Agent Memory System

独立的三层记忆系统，为多Agent提供统一的记忆管理服务。

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Chroma](https://img.shields.io/badge/vector_db-Chroma-green.svg)](https://www.trychroma.com/)
[![NetworkX](https://img.shields.io/badge/graph-NetworkX-orange.svg)](https://networkx.org/)

## 📋 目录

- [系统概述](#-系统概述)
- [核心特性](#-核心特性)
- [架构设计](#-架构设计)
- [API接口](#-api接口)
- [数据结构](#-数据结构)
- [快速开始](#-快速开始)
- [配置指南](#-配置指南)
- [实施路线图](#-实施路线图)

---

## 🌟 系统概述

本记忆系统是一个**独立的微服务**，通过RESTful API为多个Agent提供记忆管理能力。系统采用三层记忆架构，灵活支持不同的记忆存储和检索策略。

### 设计原则

- ✅ **独立性**：与Agent系统解耦，通过API通信
- ✅ **可扩展性**：支持多Agent并发访问
- ✅ **高性能**：向量检索 + 图数据库混合查询
- ✅ **可追溯性**：记忆压缩保留溯源信息
- ✅ **灵活性**：支持自定义记忆策略

---

## 🎯 核心特性

### 三层记忆架构

| 层级 | 容量 | 加载方式 | 存储介质 | 作用 |
|------|------|---------|---------|------|
| **近期记忆** | 50条/8K tokens | 完整加载 | 内存 | 保持对话连贯性 |
| **中期记忆** | 无限 | 动态检索 | Chroma + NetworkX | 结构化事件存储 |
| **长期记忆** | 无限 | 核心固定+专业动态 | Chroma + SQLite | 抽象知识和经验 |

### 核心功能

- 🔄 **自动记忆流转**：近期→中期→长期的智能压缩
- 🔍 **混合检索**：向量相似度 + 知识图谱路径查询
- ⏰ **时间衰减**：记忆重要性随时间自然衰减
- 🎯 **上下文感知**：根据查询类型动态加载相关记忆
- 👤 **Agent隔离**：每个Agent拥有独立记忆空间
- 📊 **可视化**：记忆状态和知识图谱可视化

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Applications                        │
│  ┌──────────┬──────────┬──────────┬──────────┬────────┐    │
│  │ Chairman │  Market  │   News   │Sentiment │ Report │    │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴───┬────┘    │
└───────┼──────────┼──────────┼──────────┼─────────┼─────────┘
        │          │          │          │         │
        └──────────┴──────────┴──────────┴─────────┘
                            │
                    HTTP/REST API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Memory System (FastAPI Service)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Layer                             │ │
│  │  - POST /memory/add                                     │ │
│  │  - GET  /memory/retrieve                                │ │
│  │  - GET  /memory/context                                 │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │              Memory Manager Layer                       │ │
│  │  - WorkingMemory (近期记忆)                             │ │
│  │  - EpisodicMemory (中期记忆)                            │ │
│  │  - SemanticMemory (长期记忆)                            │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │               Storage Layer                             │ │
│  │  ┌──────────┬──────────────┬────────────────────────┐  │ │
│  │  │ In-Memory│ ChromaDB     │ NetworkX + SQLite      │  │ │
│  │  │ (deque)  │ (向量存储)    │ (图 + 结构化存储)       │  │ │
│  │  └──────────┴──────────────┴────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
memory_system/
├── README.md                    # 本文档
├── DESIGN.md                    # 详细设计文档
├── requirements.txt             # Python依赖
├── pyproject.toml              # 项目配置
│
├── api/                        # API层
│   ├── __init__.py
│   ├── server.py               # FastAPI服务器
│   ├── routes.py               # API路由定义
│   └── schemas.py              # Pydantic数据模型
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── manager.py              # 记忆管理器
│   ├── working_memory.py       # 近期记忆
│   ├── episodic_memory.py      # 中期记忆
│   ├── semantic_memory.py      # 长期记忆
│   └── compressor.py           # 记忆压缩器
│
├── storage/                    # 存储层
│   ├── __init__.py
│   ├── vector_store.py         # Chroma向量数据库
│   ├── graph_store.py          # NetworkX知识图谱
│   └── sql_store.py            # SQLite结构化存储
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── embeddings.py           # 向量嵌入
│   ├── tokenizer.py            # Token计数
│   └── event_extractor.py      # 事件抽取
│
├── config/                     # 配置文件
│   ├── __init__.py
│   └── settings.py             # 系统配置
│
├── tests/                      # 测试
│   ├── test_api.py
│   ├── test_memory.py
│   └── test_compression.py
│
└── examples/                   # 示例代码
    ├── basic_usage.py
    └── agent_integration.py
```

---

## 📡 API接口

### 1. 添加记忆

**POST** `/memory/add`

```json
{
  "agent_id": "market_agent",
  "memory_type": "conversation",
  "content": {
    "role": "user",
    "message": "Apple股票怎么样？",
    "timestamp": "2025-12-07T10:00:00Z"
  },
  "metadata": {
    "session_id": "sess_123",
    "importance": 0.8
  }
}
```

**响应**：
```json
{
  "status": "success",
  "memory_id": "mem_abc123",
  "stored_in": ["working_memory", "episodic_memory"]
}
```

---

### 2. 检索记忆

**GET** `/memory/retrieve`

**参数**：
- `agent_id`: Agent ID
- `query`: 查询文本
- `memory_types`: 记忆类型（working/episodic/semantic）
- `top_k`: 返回数量
- `time_range`: 时间范围（可选）

```json
{
  "agent_id": "market_agent",
  "query": "Apple股票分析",
  "memory_types": ["episodic", "semantic"],
  "top_k": 5
}
```

**响应**：
```json
{
  "status": "success",
  "results": [
    {
      "memory_id": "mem_xyz",
      "type": "episodic",
      "content": "...",
      "score": 0.92,
      "timestamp": "2025-12-01T10:00:00Z"
    }
  ]
}
```

---

### 3. 获取完整上下文

**GET** `/memory/context`

**参数**：
- `agent_id`: Agent ID
- `query`: 当前查询
- `session_id`: 会话ID（可选）

```json
{
  "agent_id": "market_agent",
  "query": "分析Tesla股票",
  "session_id": "sess_123"
}
```

**响应**：
```json
{
  "status": "success",
  "context": {
    "system_prompt": "...",
    "core_principles": "...",
    "working_memory": [...],
    "episodic_memory": [...],
    "semantic_memory": [...]
  },
  "token_usage": {
    "core_principles": 500,
    "working_memory": 7800,
    "episodic_memory": 1900,
    "semantic_memory": 450,
    "total": 10650
  }
}
```

---

### 4. 压缩记忆

**POST** `/memory/compress`

```json
{
  "agent_id": "market_agent",
  "time_window_days": 30,
  "force": false
}
```

**响应**：
```json
{
  "status": "success",
  "compressed": {
    "episodic_count": 1500,
    "semantic_count": 12,
    "compression_ratio": 125.0
  }
}
```

---

### 5. 获取记忆统计

**GET** `/memory/stats`

```json
{
  "agent_id": "market_agent"
}
```

**响应**：
```json
{
  "status": "success",
  "stats": {
    "working_memory": {
      "count": 50,
      "tokens": 7800
    },
    "episodic_memory": {
      "count": 3200,
      "oldest": "2025-11-01T00:00:00Z"
    },
    "semantic_memory": {
      "core_principles": 8,
      "experiences": 45
    }
  }
}
```

---

## 📊 数据结构

### 近期记忆（Working Memory）

```python
{
  "id": "work_mem_123",
  "agent_id": "market_agent",
  "session_id": "sess_123",
  "timestamp": "2025-12-07T10:00:00Z",
  "role": "user",  # user/agent/system
  "content": "Apple股票怎么样？",
  "tokens": 156,
  "importance": 0.8,
  "protected": false
}
```

### 中期记忆（Episodic Memory）

```python
{
  "id": "epi_mem_456",
  "agent_id": "market_agent",
  "event_type": "stock_analysis",
  "entities": ["Apple", "AAPL"],
  "relations": [
    {"subject": "Apple", "predicate": "has_pe", "object": 28.5},
    {"subject": "User", "predicate": "interested_in", "object": "Apple"}
  ],
  "key_findings": {
    "price": 180.23,
    "pe_ratio": 28.5,
    "sentiment": "positive"
  },
  "timestamp": "2025-12-07T10:00:00Z",
  "importance": 0.85,
  "embedding": [0.123, -0.456, ...],  # 1536维向量
  "access_count": 3,
  "last_accessed": "2025-12-07T11:00:00Z"
}
```

### 长期记忆（Semantic Memory）

```python
{
  "id": "sem_mem_789",
  "agent_id": "market_agent",
  "category": "core_principle",  # core_principle/experience_rule/user_preference
  "title": "高PE股票风险提示",
  "content": "当股票PE>30时，需要额外说明风险并对比行业平均水平",
  "applicable_scenarios": ["stock_analysis", "investment_advice"],
  "confidence": 0.92,
  "source_events": ["epi_mem_123", "epi_mem_456", ...],
  "created_at": "2025-11-01T00:00:00Z",
  "embedding": [0.234, -0.567, ...]
}
```

---

## 🚀 快速开始

### 安装

```bash
# 1. 进入项目目录
cd /Users/weizhifeng/github/stock-trading-platform/memory_system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python -m core.init_db

# 4. 启动服务
python -m api.server
```

服务将在 `http://localhost:8001` 启动

### 基础使用

```python
import requests

# 1. 添加记忆
response = requests.post("http://localhost:8001/memory/add", json={
    "agent_id": "market_agent",
    "memory_type": "conversation",
    "content": {
        "role": "user",
        "message": "Apple股票怎么样？"
    }
})

# 2. 获取上下文
response = requests.get("http://localhost:8001/memory/context", params={
    "agent_id": "market_agent",
    "query": "分析Tesla股票"
})

context = response.json()["context"]
```

---

## ⚙️ 配置指南

### 环境变量

```bash
# .env
MEMORY_SYSTEM_PORT=8001
CHROMA_PERSIST_DIR=./data/chroma
SQLITE_DB_PATH=./data/memory.db
EMBEDDING_MODEL=openai/text-embedding-3-small
OPENAI_API_KEY=sk-...
```

### 配置文件

```yaml
# config/settings.yaml
memory:
  working:
    max_items: 50
    max_tokens: 8000
  
  episodic:
    compression_threshold: 5000
    time_decay_rate: 0.1
  
  semantic:
    core_principles_limit: 10
    clustering_k: 10

api:
  host: "0.0.0.0"
  port: 8001
  cors_origins: ["*"]

storage:
  chroma:
    persist_directory: "./data/chroma"
  sqlite:
    database_path: "./data/memory.db"
```

---

## 🛠️ Agent集成示例

### Python SDK

```python
from memory_system.client import MemoryClient

# 初始化客户端
memory = MemoryClient(
    base_url="http://localhost:8001",
    agent_id="market_agent"
)

# 添加对话记忆
memory.add_conversation(
    role="user",
    message="Apple股票怎么样？",
    importance=0.8
)

# 获取完整上下文
context = memory.get_context(
    query="分析Tesla股票",
    session_id="sess_123"
)

# 使用上下文构建Prompt
prompt = f"""
{context['system_prompt']}

{context['core_principles']}

## 近期对话：
{context['working_memory']}

## 相关历史：
{context['episodic_memory']}

## 当前查询：
分析Tesla股票
"""
```

### Google ADK集成

```python
from google import genai
from memory_system.client import MemoryClient

# 初始化记忆客户端
memory = MemoryClient(agent_id="market_agent")

# 在Agent中集成
def agent_with_memory(user_query: str):
    # 1. 获取记忆上下文
    context = memory.get_context(query=user_query)
    
    # 2. 构建增强的系统提示
    enhanced_system = f"""
{base_system_prompt}

{context['core_principles']}
"""
    
    # 3. 添加检索到的记忆到上下文
    messages = context['working_memory'] + [
        {"role": "system", "content": context['episodic_memory']},
        {"role": "user", "content": user_query}
    ]
    
    # 4. 调用LLM
    response = agent.generate(messages=messages)
    
    # 5. 保存新记忆
    memory.add_conversation(role="agent", message=response)
    
    return response
```

---

## 📈 实施路线图

### Phase 1: MVP（2-3周）
- ✅ 基础API框架（FastAPI）
- ✅ 近期记忆（内存队列）
- ✅ Chroma向量数据库集成
- ✅ 基础检索功能

### Phase 2: 核心功能（3-4周）
- ✅ 事件抽取器
- ✅ NetworkX知识图谱
- ✅ 混合检索（向量+图）
- ✅ 时间衰减机制

### Phase 3: 高级特性（4-6周）
- ✅ k-Means聚类压缩
- ✅ LLM自省总结
- ✅ 混合触发策略
- ✅ Agent隔离和权限

### Phase 4: 优化与监控（持续）
- ✅ 性能优化
- ✅ 可视化界面
- ✅ 监控和日志
- ✅ A/B测试

---

## 📚 相关文档

- [详细设计文档](DESIGN.md)
- [API文档](docs/API.md)
- [数据结构文档](docs/DATA_STRUCTURES.md)
- [集成指南](docs/INTEGRATION.md)

---

## 🤝 贡献

欢迎贡献！请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

**Happy Coding! 🚀**
