# 🤖 AI-fundin - 智能股票分析系统

基于多Agent协作和AI的股票市场数据分析平台，提供实时行情、K线图表、AI智能分析、市场情绪分析等功能。

## 🌟 项目特色

- **多市场支持**: A股、美股、港股全覆盖
- **真实数据**: 对接Yahoo Finance等权威数据源，确保数据真实性
- **多Agent协作**: 基于LangGraph的Boardroom架构，Receptionist-Chairman-Specialists-Critic协作模式
- **AI智能分析**: 集成Claude AI和DeepSeek大模型，提供智能投资建议
- **市场情绪分析**: 基于FinBERT模型的专业金融情绪分析，自动抓取新浪财经等新闻源 🆕
- **可视化图表**: TradingView集成，专业级K线图表
- **响应式设计**: 现代化的用户界面，适配各种设备
- **A2A协议支持**: 支持Google A2A (Agent-to-Agent) 协议，实现Agent间互操作性

## 🏗️ 系统架构

### 技术栈
- **前端**: React + TypeScript + Vite + Tailwind CSS v4 + Lucide图标
- **后端**: Python + FastAPI + LangGraph + 多Agent协作系统
- **数据源**: Yahoo Finance、新浪财经等权威数据源
- **AI集成**: DeepSeek大模型 + Claude AI对话助手
- **图表**: TradingView轻量级图表库
- **Agent框架**: LangChain + LangGraph实现多Agent协作
- **协议**: 标准REST API + Google A2A协议

### 系统架构图
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          前端层 (Frontend Layer)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  React + TypeScript + Vite + Tailwind CSS v4                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────┐ │
│  │  MarketQuery │  StockSearch │  MacroData   │   KLineChart │  AIChat  │ │
│  │    Page      │    Page      │    Page      │ Component  │ Component│ │
│  └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴────┬─────┘ │
│         │              │              │              │            │       │
│  ┌──────┴──────────────┴──────────────┴──────────────┴────────────┴────┐  │
│  │                    API Services Layer                           │  │
│  │              stockAPI.ts • agentAPI.ts • macroAPI.ts            │  │
│  └────────────────────────────┬──────────────────────────────────────┘  │
└───────────────────────────────┼───────────────────────────────────────────┘
                                │
┌───────────────────────────────┼───────────────────────────────────────────┐
│                          API Gateway Layer                                │
├───────────────────────────────┼───────────────────────────────────────────┤
│  FastAPI Server (Port 8001)   │        Backend Proxy (Port 8000)        │
│  ┌────────────┬──────────────┼──────────────┬────────────────────────┐ │
│  │  /api/chat │  /a2a/*     │ │ /api/market/* │ /api/macro/*          │ │
│  └──────┬─────┴──────┬───────┼───────┬──────┼────────┬──────────────┘ │
│         │          │       │       │      │        │                │
│  ┌──────┴──────────┴───────┼───────┼──────┼────────┼──────────────┐ │
│  │    Agent Core (LangGraph) │       │        Direct Skill Calls │  │
│  │  Receptionist → Chairman  │       │                               │  │
│  │        ↓                    │       │                               │  │
│  │  Specialists → Critic      │       │                               │  │
│  └────────────┬───────────────┼───────┼──────┼──────────────────────┘  │
└───────────────┼───────────────┼───────┼──────┼─────────────────────────┘
                │               │       │      │
┌───────────────┼───────────────┼───────┼──────┼─────────────────────────┐
│          Skills/Tools Layer  │       │      │                         │
├───────────────┼───────────────┼───────┼──────┼─────────────────────────┤
│ ┌────────────▼┐ ┌───────────▼┐ ┌────▼┐ ┌───▼┐ ┌────────▼┐            │
│ │MarketData  │ │Sentiment   │ │Macro│ │Web │ │Finnhub  │            │
│ │   Skill    │ │  Analysis  │ │Data │ │Search│ │ Client  │            │
│ └──────┬──────┘ └──────┬─────┘ └──┬──┘ └──┬──┘ └────┬────┘            │
│        │               │          │       │        │                 │
│  ┌─────▼───────────────▼──────────▼───────▼────────▼────────────┐    │
│  │                    Data Sources Layer                       │    │
│  │  Yahoo Finance • 新浪财经 • FRED • Finnhub • Reddit API    │    │
│  └───────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────┘
```

### 多Agent协作流程 (Boardroom Pattern)
```
用户请求 → Receptionist(意图分析) → Research Brief
                ↓
            Chairman(任务规划) → 分配Specialist
                ↓
            Specialists(具体执行) → 收集证据
                ↓
            Critic(综合分析) → 最终响应
```

### Agent角色说明
- **Receptionist**: 接待员，分析用户意图，生成研究简报
- **Chairman**: 主席，基于研究简报规划任务，分配专家Agent
- **Specialists**: 专家团队，执行具体任务
  - *MarketDataInvestigator*: 市场数据查询
  - *SentimentInvestigator*: 情绪分析
  - *MacroDataInvestigator*: 宏观经济数据
  - *WebSearchInvestigator*: 网络搜索
- **Critic**: 评论家，综合所有证据生成最终回答

### A2A协议架构
每个Agent都可作为独立的A2A服务：
```
GET  /a2a/{agent}/.well-known/agent.json  # 获取Agent能力描述
POST /a2a/{agent}/run                     # 执行Agent任务
```

### 数据流

#### 1. 前端数据流
```
用户交互 → React组件 → API服务 → HTTP请求 → 后端API
    ↓
状态更新 ← 数据处理 ← 响应解析 ←  ←  ← 后端响应
```

#### 2. Agent系统数据流
```
用户查询 → Receptionist → Research Brief → Chairman → 任务分配
    ↓
工具调用 ← Specialists ← 证据收集 ←  ←  ← 数据源
    ↓
最终响应 ← Critic ← 综合分析 ←  ←  ← 所有证据
```

#### 3. 直接API调用流
```
前端请求 → Backend Proxy → Skill直接调用 → 数据源 → 原始数据
    ↓
格式化响应 ← 数据处理 ←  ←  ←  ←  ←  ← 数据获取
```

## 📈 当前功能进度

### ✅ 已完成功能

#### 1. 多Agent股票分析系统 🆕
- [x] **Boardroom架构**: Receptionist-Chairman-Specialists-Critic协作模式
- [x] **意图识别**: Receptionist智能分析用户查询意图
- [x] **任务规划**: Chairman基于研究简报动态分配任务
- [x] **专家执行**: 多Specialist并行执行具体任务
- [x] **综合分析**: Critic综合所有证据生成最终报告
- [x] **ReAct模式**: 专家Agent具备推理-行动能力
- [x] **流式输出**: SSE支持实时流式响应
- [x] **A2A协议**: Google A2A协议完整实现

#### 2. 核心市场数据功能
- [x] **实时行情查询**: 支持A股、美股、港股实时数据获取
- [x] **多数据源集成**: Yahoo Finance + 新浪财经双数据源保障
- [x] **智能股票搜索**: 支持股票代码、中文公司名称搜索
- [x] **错误处理机制**: 完善的异常处理和降级策略
- [x] **数据验证优化**: 放宽价格范围验证，支持真实市场数据变化
- [x] **高频限流优化**: 提高开发环境请求限制（1000次/小时）

#### 3. 历史数据系统
- [x] **真实历史数据**: 30天历史K线数据，来源真实市场
- [x] **历史数据API**: `/api/market/historical/{symbol}?period=30d`
- [x] **数据格式标准化**: 统一的OHLCV数据格式
- [x] **数据质量保障**: 真实数据源，拒绝模拟数据
- [x] **交易日过滤**: 自动过滤非交易日（周末、节假日）

#### 4. AI对话分析系统
- [x] **AI聊天侧边栏**: 集成Claude AI智能助手
- [x] **历史数据表格**: 自动生成15天开盘收盘价表格
- [x] **智能分析**: 基于真实数据的AI投资建议
- [x] **数据溯源**: 明确标注数据来源，确保透明度

#### 5. 市场情绪分析系统
- [x] **FinBERT情绪分析**: 使用专业金融BERT模型分析市场情绪
- [x] **新闻自动抓取**: 从新浪财经等权威源自动获取最新新闻
- [x] **情绪评分**: 0-100分量化情绪，Bullish/Neutral/Bearish评级
- [x] **关键驱动因素**: 自动提取影响情绪的关键新闻
- [x] **多源支持**: 支持Reddit社交媒体分析（可选配置）
- [x] **实时更新**: 基于最新新闻实时分析市场情绪

#### 6. 宏观经济数据系统 🆕
- [x] **FRED数据集成**: 美国联邦储备银行经济数据API
- [x] **FedWatch工具**: 联邦基金利率概率分析
- [x] **CME利率概率**: 基于期货市场的加息降息预期
- [x] **经济日历**: 重要经济指标发布时间表
- [x] **数据可视化**: 专业级宏观经济图表

#### 7. 可视化图表
- [x] **TradingView集成**: 专业级K线图表组件（lightweight-charts v5）
- [x] **图表缩放**: 支持鼠标滚轮缩放和拖拽平移
- [x] **日期范围选择**: 7天、14天、30天数据快速切换
- [x] **交易日显示**: Business Day模式自动跳过周末
- [x] **错误处理**: 图表异常自动降级处理
- [x] **响应式设计**: 适配移动端和桌面端

#### 8. 系统架构优化
- [x] **限流机制**: 基于令牌桶的API限流保护（可配置）
- [x] **熔断机制**: 数据源异常时的自动降级
- [x] **缓存策略**: 智能缓存减少API调用
- [x] **日志监控**: 完整的请求日志和错误追踪
- [x] **JSON序列化优化**: 统一处理datetime等特殊类型

#### 9. 前端UI优化
- [x] **Tailwind CSS v4**: 现代化CSS框架升级
- [x] **Lucide图标**: 替换传统图标库为现代化图标
- [x] **响应式布局**: 优化的侧边栏和导航栏设计
- [x] **专业配色**: 金融级配色方案（Slate/Blue主题）

### 🔧 已知问题与待优化事项
- [ ] **技术指标分析**: MACD、KDJ、RSI等专业指标
- [ ] **基本面数据展示**: 财务报表、估值指标可视化
- [ ] **市场热力图**: 板块轮动和热点追踪
- [ ] **自选股功能**: 个人股票组合管理
- [ ] **数据缓存优化**: 减少重复API调用

## 🚀 快速开始

### 环境要求
- Node.js 18+ 
- Python 3.9+
- 8000端口(后端代理)和8001端口(Agent API)可用

### 启动步骤
```bash
# 1. 克隆项目并安装依赖
git clone <repository-url>
cd AI-fundin

# 2. 安装Python依赖（推荐使用虚拟环境）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动后端代理服务 (端口8000)
# 使用虚拟环境的Python
venv/bin/python backend/api_server.py --port 8000
# 或者直接在backend目录下运行
cd backend && python api_server.py

# 4. 启动Agent API服务 (端口8001)
# 在另一个终端窗口
cd agent
python main.py

# 5. 启动前端开发服务器（新终端窗口）
cd frontendV2
npm install
npm run dev

# 6. 访问应用
# 前端地址：http://localhost:3005（端口会自动递增）
# 后端代理API：http://localhost:8000
# Agent API：http://localhost:8001
# API文档：http://localhost:8001/docs
```

### 系统启动顺序
```
1. 后端代理服务 (8000) → 提供市场数据、宏观数据等直接API
2. Agent API服务 (8001) → 提供多Agent协作分析能力
3. 前端开发服务器 (3000+) → 用户界面
```

### 服务端口说明
- **8000**: 后端代理服务 - 直接调用Skills获取数据
- **8001**: Agent API服务 - 多Agent协作分析
- **3000+**: 前端开发服务器 - React应用

### 配置说明
Agent系统配置文件：`agent/config.yaml`
```yaml
llm:
  api_key: "your-api-key"
  api_base: "https://api.siliconflow.cn/v1"
  model: "deepseek-ai/DeepSeek-V3.1-Terminus"
  
server:
  host: "0.0.0.0"
  port: 8001
```

### 常见问题

**Q: 启动时提示端口被占用**
A: 检查端口使用情况：
```bash
lsof -t -i:8000  # 检查8000端口
lsof -t -i:8001  # 检查8001端口
lsof -t -i:3000  # 检查3000端口
```

**Q: Agent API启动失败**
A: 检查配置文件`agent/config.yaml`中的API密钥是否正确

**Q: 前端无法连接后端**
A: 确保后端代理服务(8000)和Agent API(8001)都已启动

## 📡 API接口文档

### 后端代理API (端口8000)
```
GET  /api/market-data/hot              # 获取热门股票
GET  /api/market-data/search           # 搜索股票
GET  /api/market-data/quote/{symbol}    # 获取实时报价
GET  /api/market-data/historical/{symbol}?period=30d  # 获取历史数据
GET  /api/macro/fed-watch              # 获取FedWatch数据
GET  /api/macro/economic-calendar        # 获取经济日历
```

### Agent API (端口8001)
```
POST /api/chat                           # 标准对话接口
GET  /a2a/{agent}/.well-known/agent.json # 获取Agent能力描述
POST /a2a/{agent}/run                    # 执行Agent任务
```

支持的Agent类型：
- `marketdatainvestigator`: 市场数据调查员
- `sentimentinvestigator`: 情绪分析调查员  
- `macrodatanvestigator`: 宏观数据调查员
- `websearchinvestigator`: 网络搜索调查员

### 前端页面路由
```
/                 # 首页
/market-query     # 市场数据查询
/stock-search     # 股票搜索
/macro-data       # 宏观经济数据
/debug            # 调试页面
```

## 🔧 技术架构详解

### 前端架构
```
frontendV2/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── AIChat/         # AI对话组件
│   │   ├── KLineChart/     # K线图表组件
│   │   ├── Council/        # 多Agent协作展示
│   │   └── ...
│   ├── pages/              # 页面组件
│   │   ├── MarketQueryPage.tsx
│   │   ├── StockSearchPage.tsx
│   │   ├── MacroDataPage.tsx
│   │   └── ...
│   ├── services/           # API服务层
│   │   ├── stockAPI.ts     # 股票数据API
│   │   ├── agentAPI.ts     # Agent API
│   │   └── macroAPI.ts     # 宏观数据API
│   └── utils/              # 工具函数
```

### 后端代理架构
```
backend/
├── api_server.py           # API服务器主入口
└── 直接调用Skills获取数据
```

### Agent系统架构
```
agent/
├── main.py                 # FastAPI应用入口
├── api/
│   ├── routes.py           # REST API路由
│   └── a2a.py              # A2A协议实现
├── core/
│   ├── agent.py             # 主Agent类
│   ├── graph.py             # LangGraph定义
│   ├── state.py             # 状态管理
│   └── agents/              # 各Agent实现
│       ├── receptionist.py
│       ├── chairman.py
│       ├── critic.py
│       ├── market.py
│       ├── sentiment.py
│       ├── macro.py
│       └── web_search.py
└── utils/                   # 工具函数
```

### Skills架构
```
skills/
├── market_data_tool/        # 市场数据工具
├── sentiment_analysis_tool/ # 情绪分析工具
├── macro_data_tool/         # 宏观数据工具
└── web_search_tool/         # 网络搜索工具
```

### 数据架构
```
多层级数据验证和缓存：
数据源 → Skills → 后端代理/Agent → 前端 → 用户界面
  ↓         ↓           ↓           ↓        ↓
原始数据 → 标准化 → 业务逻辑处理 → 组件状态 → 可视化展示
```

## 🎯 未来功能规划

### 近期目标 (1-2个月)
- [ ] **多Agent优化**: 提升任务规划和执行效率
- [ ] **A2A生态**: 支持更多外部Agent系统集成
- [ ] **实时推送**: WebSocket支持实时数据推送
- [ ] **用户系统**: 个性化设置和历史记录

### 中期目标 (3-6个月)
- [ ] **量化策略**: 基于多Agent的量化交易策略
- [ ] **组合管理**: 自选股组合和风险管理
- [ ] **社交功能**: 投资者社区和策略分享
- [ ] **移动端**: React Native移动应用

### 长期愿景 (6-12个月)
- [ ] **预测模型**: 多因子股价预测模型
- [ ] **智能投顾**: 个性化投资建议和资产配置
- [ ] **机构服务**: 为专业机构提供API服务
- [ ] **全球扩展**: 支持更多国际市场

## 🔒 安全与合规

### 数据安全
- **API密钥管理**: 配置文件分离，支持环境变量
- **请求限流**: 基于令牌桶的API限流保护
- **错误处理**: 完善的异常处理和降级机制
- **日志监控**: 详细的请求日志和错误追踪

### 合规声明
- **数据来源**: 所有数据来自公开API和授权数据源
- **使用限制**: 仅限学习和研究使用，不构成投资建议
- **免责声明**: 明确标注投资风险，提醒用户谨慎决策

### A2A安全
- **服务发现**: 标准化的Agent能力描述
- **访问控制**: 支持中间件级别的权限验证
- **通信安全**: 建议生产环境使用HTTPS

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发规范
- 遵循TypeScript严格模式和Python类型注解
- 编写单元测试和集成测试
- 保持代码注释清晰完整
- 遵循项目现有的代码风格
- 遵循Agent开发最佳实践
- 保持A2A协议兼容性

### 提交规范
- 使用清晰的提交信息
- 关联相关Issue
- 提供详细的变更说明
- 更新相关文档

## 📄 开源协议

本项目采用MIT协议开源，详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交GitHub Issue
- 发送详细的功能建议
- 参与技术讨论和架构设计

---

**⚠️ 免责声明**: 本项目仅供学习和研究使用，所有数据和分析结果不构成投资建议。系统采用多Agent协作架构提供智能化分析，但投资决策仍需用户独立判断。投资有风险，入市需谨慎。

**🤖 AI声明**: 本系统集成的AI分析和预测功能仅供学习参考，不构成任何投资建议。用户应充分了解AI模型的局限性，并结合自身判断做出投资决策。
