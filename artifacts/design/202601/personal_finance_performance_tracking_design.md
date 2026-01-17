# 📈 个人理财收益率曲线追踪 (Personal Finance Performance Tracking) 设计方案

## 1. 背景与目标 (Context & Goals)
用户希望在“个人理财”页面新增一个收益率对比功能，展示四条曲线：
1. **上证指数** (Benchmark SH)
2. **深证成指** (Benchmark SZ)
3. **用户持仓收益率** (User Portfolio Return)
4. **AI 决策收益率** (AI Shadow Portfolio Return)

**核心逻辑**：
- **起点 (T0)**：从用户录入持仓的那一刻（或功能开启日）开始，四条曲线归一化为 0% (净值 1.0)。
- **AI 决策**：AI 的建议会在后台维护一个“影子账户”，该账户完全听从 AI 指令进行虚拟交易，从而形成独立的收益曲线，用于对比“如果完全听 AI 的会怎样”。
- **计算时机**：前端展示时实时计算（盘中波动），AI 调仓在当日收盘后结算。

## 2. 核心设计 (Core Design)

### 2.1 业务流程

#### A. 初始化 (T0)
- 当用户首次保存持仓时：
    1. 记录当前时间为 `start_date`。
    2. 创建 **User Portfolio** (真实持仓)。
    3. 克隆一份完全一样的 **Shadow Portfolio** (AI 影子持仓)。
    4. 初始化 **PerformanceHistory** (净值表)，四者净值均为 1.0。

#### B. 每日/实时计算 (Real-time Calculation)
- **指数**：拉取历史数据 + 实时行情，计算相对于 `start_date` 的涨跌幅。
- **用户持仓 (User)**：
    - 采用 **单位净值法 (Unit Net Value)** 计算。
    - `今日收益率` = `(今日总市值 - 今日净投入 + 昨日分红) / 昨日总市值`
    - `当前净值` = `昨日净值 * (1 + 今日收益率)`
    - *注：若用户盘中修改持仓（加减仓），视为“净投入”变动，不影响净值走势，只影响总资产。*
- **AI 影子账户 (AI Shadow)**：
    - 基于数据库中 `ShadowPortfolio` 的当前持仓，结合实时价格计算净值。
    - 逻辑同上。

#### C. AI 影子交易 (Shadow Trading)
- **触发条件**：用户触发 AI 分析，且 AI 生成了 `Decision` (Buy/Sell/Adjust)。
- **执行逻辑**：
    - **即时成交 (Real-time Execution)**：为简化系统复杂度并支持惰性计算，AI 建议生成后，影子账户**立即**按当前市场价格（Last Price）完成虚拟调仓。
    - **记录变动**：更新 `ShadowPortfolio` 的持仓结构，并记录更新时间。

#### D. 数据补全机制 (Lazy Data Backfill)
- **核心理念**：**完全摒弃后台定时任务**。所有数据的计算、补全、落库均由**用户前端查询 (On-Demand)** 触发。
- **场景**：用户多日未登录（如上次 1月1日，今日 1月10日）。
- **逻辑**：
    1.  **检测断档**：API 收到请求，发现数据库最新 `PerformanceHistory` 是 1月1日。
    2.  **获取行情**：后端批量拉取 1月2日-1月9日 的指数行情和用户/影子持仓股票的日线数据。
    3.  **批量计算**：
        - 这里的持仓结构假设为“最后一次已知状态”（即 1月1日的状态，除非期间有离线操作，但当前设计假设无离线操作）。
        - 结合历史价格，算出 1月2日-1月9日 的每日净值。
    4.  **落库与返回**：将补全的数据存入 DB，并计算 1月10日 的实时净值一并返回。

### 2.2 数据模型设计 (Schema Design)

在 `backend/app/agents/personal_finance/db_models.py` 中新增：

```python
class ShadowPortfolio(SQLModel, table=True):
    """
    AI 影子账户，结构与 Portfolio 类似，但完全由 AI 控制。
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    cash_balance: float = Field(default=0.0)
    # 关联 ShadowAssets (需新增 ShadowAsset 表或复用 Asset 表并加 type 区分，建议新建以隔离)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ShadowAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="shadowportfolio.id")
    symbol: str
    quantity: float
    avg_cost: float # 虚拟持仓成本
    
class PerformanceHistory(SQLModel, table=True):
    """
    每日净值历史记录 (Daily NAV History)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    date: str = Field(index=True)  # YYYY-MM-DD
    
    # 净值 (Net Asset Value), 初始为 1.0
    nav_user: float
    nav_ai: float
    nav_sh: float # 上证
    nav_sz: float # 深证
    
    # 辅助字段，用于校验
    total_assets_user: float
    total_assets_ai: float
```

### 2.3 接口设计 (API Design)

**GET /api/personal-finance/performance**
- **Params**: `user_id`
- **Response**:
    ```json
    {
      "start_date": "2026-01-10",
      "series": [
        {"date": "2026-01-10", "nav_user": 1.0, "nav_ai": 1.0, "nav_sh": 1.0, "nav_sz": 1.0},
        {"date": "2026-01-11", "nav_user": 1.02, "nav_ai": 1.01, "nav_sh": 1.005, "nav_sz": 0.99},
        ...
        {"date": "2026-01-17", "nav_user": 1.05, "nav_ai": 1.08, "nav_sh": 1.01, "nav_sz": 1.02} 
        // 最后一个点可以是实时的
      ]
    }
    ```

## 3. 影响范围 (Impact)
- **DB**: 新增 3 张表 (`ShadowPortfolio`, `ShadowAsset`, `PerformanceHistory`)。
- **Backend**:
    - `PersonalFinanceAgent`: 需增加初始化 Shadow 账户的逻辑。
    - `ReviewAgent` / `Orchestrator`: 需增加每日收盘结算的定时任务（或懒加载结算逻辑）。
    - API 层新增数据获取接口，包含**补全逻辑**。
- **Frontend**: 新增 ECharts 折线图组件渲染 4 条曲线。

## 4. 潜在风险与应对
- **数据缺失**：如果某天没有拉取到行情，净值如何计算？ -> 方案：沿用上一日净值。
- **分红拆股**：真实世界的除权除息会影响股价。 -> 方案：初期版本忽略分红，直接按价格计算；后续对接 AkShare 的复权数据 (Adj Close)。
