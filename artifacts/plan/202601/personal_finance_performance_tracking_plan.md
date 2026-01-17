# Personal Finance Performance Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a performance tracking system with 4 curves (User, AI Shadow, SH Index, SZ Index) using Shadow Account and Unit Net Value methods with lazy backfill.

**Architecture:**
- **Database**: 3 new tables (`ShadowPortfolio`, `ShadowAsset`, `PerformanceHistory`) using SQLModel.
- **Backend**:
    - **Shadow Logic**: Parallel portfolio that executes AI decisions immediately.
    - **Performance Logic**: On-demand calculation of NAV (Net Asset Value) with lazy backfill for missing history.
- **Frontend**: ECharts visualization of the 4 normalized return curves.

**Tech Stack**: Python (FastAPI, SQLModel), React, ECharts.

---

### Task 1: Database Models

**Files:**
- Modify: `backend/app/agents/personal_finance/db_models.py`
- Test: `backend/tests/test_personal_finance_persistence.py`

**Step 1: Write the failing test for new models**

```python
# backend/tests/test_personal_finance_persistence.py (append)
def test_shadow_portfolio_models(session):
    from app.agents.personal_finance.db_models import ShadowPortfolio, ShadowAsset, PerformanceHistory
    
    # Test Shadow Portfolio creation
    shadow = ShadowPortfolio(user_id="test_user", cash_balance=10000.0)
    session.add(shadow)
    session.commit()
    session.refresh(shadow)
    assert shadow.id is not None
    assert shadow.cash_balance == 10000.0

    # Test Shadow Asset
    asset = ShadowAsset(portfolio_id=shadow.id, symbol="AAPL", quantity=10, avg_cost=150.0)
    session.add(asset)
    session.commit()
    
    # Test Performance History
    perf = PerformanceHistory(
        user_id="test_user", 
        date="2026-01-01", 
        nav_user=1.0, 
        nav_ai=1.0, 
        nav_sh=1.0, 
        nav_sz=1.0,
        total_assets_user=10000.0,
        total_assets_ai=10000.0
    )
    session.add(perf)
    session.commit()
    assert perf.id is not None
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_personal_finance_persistence.py::test_shadow_portfolio_models -v`
Expected: FAIL (ImportError or NameError)

**Step 3: Write minimal implementation**

```python
# backend/app/agents/personal_finance/db_models.py (add classes)
class ShadowPortfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    cash_balance: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ShadowAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="shadowportfolio.id")
    symbol: str
    quantity: float
    avg_cost: float

class PerformanceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    date: str = Field(index=True)
    nav_user: float
    nav_ai: float
    nav_sh: float
    nav_sz: float
    total_assets_user: float
    total_assets_ai: float
```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_personal_finance_persistence.py::test_shadow_portfolio_models -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/agents/personal_finance/db_models.py backend/tests/test_personal_finance_persistence.py
git commit -m "feat: add shadow portfolio and performance history models"
```

---

### Task 2: Shadow Portfolio Initialization

**Files:**
- Modify: `backend/app/agents/personal_finance/agent.py` (or wherever portfolio init happens)
- Test: `backend/tests/test_personal_finance_agent.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_personal_finance_agent.py
def test_init_shadow_portfolio_on_creation(session):
    # Mocking necessary parts or using integration test
    # This assumes there is a function `initialize_user_portfolio`
    from app.agents.personal_finance.service import initialize_user_portfolio
    
    user_id = "new_user_shadow_test"
    initialize_user_portfolio(user_id, initial_assets=[...], session=session)
    
    # Check if Shadow Portfolio exists and matches
    shadow = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
    assert shadow is not None
    # Assert assets are cloned
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_personal_finance_agent.py -v`
Expected: FAIL

**Step 3: Write implementation**
In `initialize_user_portfolio` (or equivalent), add logic to clone `Portfolio` to `ShadowPortfolio` and `Asset` to `ShadowAsset`. Also create the first `PerformanceHistory` entry with NAV 1.0.

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_personal_finance_agent.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/agents/personal_finance/agent.py backend/tests/test_personal_finance_agent.py
git commit -m "feat: init shadow portfolio on user creation"
```

---

### Task 3: Shadow Trading Execution

**Files:**
- Modify: `backend/app/agents/personal_finance/service.py` (implement `execute_shadow_trade`)
- Test: `backend/tests/test_personal_finance_service.py`

**Step 1: Write failing test**
```python
def test_execute_shadow_trade():
    # Setup shadow portfolio with cash
    # Call execute_shadow_trade(decision="BUY AAPL 10")
    # Assert shadow asset created and cash reduced
```

**Step 2: Run test**
Expected: FAIL

**Step 3: Implement `execute_shadow_trade`**
- Parse decision (Buy/Sell)
- Get current price (mock or real)
- Update `ShadowPortfolio` cash and `ShadowAsset` quantity.

**Step 4: Run test**
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/agents/personal_finance/service.py
git commit -m "feat: implement shadow trading execution"
```

---

### Task 4: Performance Calculation & Lazy Backfill

**Files:**
- Create: `backend/app/agents/personal_finance/performance_service.py`
- Modify: `backend/app/agents/personal_finance/api.py` (to use service)
- Test: `backend/tests/test_performance_service.py`

**Step 1: Write failing test**
```python
def test_get_performance_lazy_backfill():
    # Setup history: Day 1 exists.
    # Request Day 10.
    # Mock market data for Day 2-10.
    # Call get_performance_history()
    # Assert Day 2-10 records created in DB.
    # Assert NAV calculated correctly.
```

**Step 2: Run test**
Expected: FAIL

**Step 3: Implement Service**
- `get_missing_dates(last_date, today)`
- `fetch_market_data(dates, assets)`
- `calculate_daily_nav(prev_nav, portfolio_snapshot, market_data)`
- `batch_save_history()`

**Step 4: Run test**
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/agents/personal_finance/performance_service.py
git commit -m "feat: implement performance calculation and lazy backfill"
```

---

### Task 5: Frontend Visualization

**Files:**
- Create: `frontendV2/src/components/PersonalFinance/PerformanceChart.tsx`
- Modify: `frontendV2/src/pages/PersonalFinancePage.tsx`

**Step 1: Create Chart Component**
- Use ECharts (or Recharts if preferred in project).
- Props: `data: { date: string, nav_user: number, nav_ai: number, ... }[]`
- Render 4 lines.

**Step 2: Integrate into Page**
- Fetch data from API.
- Pass to Component.

**Step 3: Commit**
```bash
git add frontendV2/src/components/PersonalFinance/PerformanceChart.tsx
git commit -m "feat: add performance chart component"
```

