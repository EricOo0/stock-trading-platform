from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Portfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    cash_balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    assets: List["Asset"] = Relationship(back_populates="portfolio")


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")

    symbol: str
    name: str
    type: str  # Stock, Fund, Crypto, Bond, Other
    market: Optional[str] = None

    quantity: float
    avg_cost: float
    current_price: float = Field(default=0.0)

    # Computed fields like total_value are not stored, calculated on fly or stored for caching?
    # Storing basic fields is enough.

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    portfolio: Optional[Portfolio] = Relationship(back_populates="assets")


class DecisionRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    symbol: str = Field(index=True)
    action: str  # buy, sell, hold
    price_at_suggestion: float
    suggested_quantity: float = Field(default=0.0) # 新增字段：建议数量
    reasoning: str  # 核心理由
    status: str = Field(default="active")  # active, closed, ignored
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 复盘字段
    review_result: Optional[str] = None # correct, incorrect
    review_comment: Optional[str] = None


class LessonRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    title: str
    description: str
    confidence: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
