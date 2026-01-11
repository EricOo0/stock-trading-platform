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
    type: str # Stock, Fund, Crypto, Bond, Other
    market: Optional[str] = None
    
    quantity: float
    avg_cost: float
    current_price: float = Field(default=0.0)
    
    # Computed fields like total_value are not stored, calculated on fly or stored for caching?
    # Storing basic fields is enough.
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    portfolio: Optional[Portfolio] = Relationship(back_populates="assets")
