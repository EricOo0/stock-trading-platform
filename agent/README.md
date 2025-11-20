# Stock Analysis Agent

基于LangChain和ReAct范式的智能股票分析Agent，支持通过MCP协议和Claude Skill进行工具调用。

## 特性

- 🤖 **ReAct Agent**: 基于推理-行动循环的智能决策
- 🔧 **工具集成**: 支持MCP协议和Claude Skill
- 🌐 **HTTP API**: FastAPI服务，易于集成
- ⚙️ **灵活配置**: 支持多种LLM后端（OpenAI格式API）

## 快速开始

### 安装依赖

```bash
cd agent
pip install -r requirements.txt
```

### 配置

复制配置文件模板并修改：

```bash
cp config.yaml.example config.yaml
```

编辑`config.yaml`，设置您的API密钥和模型配置。

### 启动服务

```bash
# 开发模式
uvicorn main:app --reload --port 8001

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 主要端点

### 对话接口
```bash
POST /api/chat
{
  "message": "帮我分析一下000001这只股票",
  "session_id": "optional-session-id"
}
```

### 配置管理
```bash
POST /api/config
{
  "llm": {
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4"
  }
}
```

### 工具列表
```bash
GET /api/tools
```

## 项目结构

```
agent/
├── core/           # 核心模块（Agent, Config, Prompts）
├── tools/          # 工具适配器（MCP, Skill）
├── api/            # FastAPI路由和模型
├── utils/          # 工具函数
└── tests/          # 测试
```

## 开发

### 运行测试

```bash
pytest tests/ -v --cov=.
```

### 添加新工具

1. 在`tools/`目录下创建新的工具适配器
2. 在`tools/manager.py`中注册工具
3. Agent会自动发现并使用新工具

## 许可

MIT License
