from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class AssetItem(BaseModel):
    id: Optional[str] = Field(None, description="Asset ID")
    symbol: Optional[str] = Field(None, description="Stock/Fund code (e.g., AAPL, sh600519)")
    name: Optional[str] = Field(None, description="Asset Name")
    type: str = Field(..., description="Asset Type: Stock, Fund, Crypto, Bond, Other")
    market: Optional[str] = Field(None, description="Market: US, CN, HK, Crypto")
    quantity: float = Field(..., description="Holding quantity")
    cost_basis: Optional[float] = Field(None, description="Cost basis per share")
    current_price: Optional[float] = Field(None, description="Current market price (if known)")
    total_value: Optional[float] = Field(None, description="Total value (quantity * price)")

class PortfolioSnapshot(BaseModel):
    assets: List[AssetItem]
    cash_balance: float = 0.0
    query: Optional[str] = Field(None, description="User query for analysis")

class PriceUpdate(BaseModel):
    price: float
    change_percent: float
    update_time: str

class PriceUpdateMap(BaseModel):
    prices: Dict[str, PriceUpdate]

class RecommendationAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    MONITOR = "monitor"

class RecommendationCard(BaseModel):
    title: str = Field(..., description="Actionable Title")
    description: str = Field(..., description="Brief explanation")
    asset_id: Optional[str] = Field(None, description="Asset Symbol")
    action: RecommendationAction = Field(..., description="Recommended Action")
    confidence_score: float = Field(..., description="Confidence 0-1")
    risk_level: str = Field(..., description="Risk Level: low, medium, high")
    
    # Optional fields from previous version if we want to keep them or strictly follow new schema
    # For now, let's stick to the prompt schema

