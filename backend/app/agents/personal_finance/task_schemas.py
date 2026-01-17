from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class WorkerType(str, Enum):
    MACRO = "macro"
    MARKET = "market"
    TECHNICAL = "technical"
    NEWS = "news"
    DAILY_REVIEW = "daily_review"


class ReplayWindow(BaseModel):
    pre: int = Field(5, description="Number of trading days before decision day")
    post: int = Field(5, description="Number of trading days after decision day")


class ReplayTarget(BaseModel):
    symbol: str
    decision_id: Optional[str] = None
    decision_time: Optional[str] = Field(
        None, description="Decision time string. Prefer ISO date or 'YYYY-MM-DD'"
    )
    window: ReplayWindow = Field(default_factory=ReplayWindow)


class ReplayFacts(BaseModel):
    """Numeric facts for replay analysis based on decision window (T-5~T+5)."""

    t_date: Optional[str] = None
    t_index: Optional[int] = None
    pre_window_return: Optional[float] = None
    post_window_return: Optional[float] = None
    post_max_drawdown: Optional[float] = None
    post_max_runup: Optional[float] = None
    volume_ratio_post: Optional[float] = None
    max_volume_spike: Optional[float] = None


class ReplayBlock(BaseModel):
    enabled: bool = False
    targets: List[ReplayTarget] = Field(default_factory=list)
    facts_by_symbol: Dict[str, ReplayFacts] = Field(default_factory=dict)
    analysis: Optional[str] = None


class LessonItem(BaseModel):
    title: str
    description: str
    applicable_conditions: Optional[str] = None
    confidence: Optional[float] = None


class HistoricalValidation(BaseModel):
    replay: ReplayBlock = Field(default_factory=ReplayBlock)
    lessons: List[LessonItem] = Field(default_factory=list)


class DecisionReviewResult(BaseModel):
    decision_id: int
    symbol: str
    original_action: str
    original_price: float
    current_price: float
    is_correct: bool
    reason: str  # 归因分析


class PreContext(BaseModel):
    query: str
    
    # New structured fields
    review_results: List[DecisionReviewResult] = Field(default_factory=list)
    reminders: List[str] = Field(default_factory=list)
    
    # Existing fields
    # precautions: List[str] = Field(default_factory=list) # Removed as requested
    lessons: List[LessonItem] = Field(default_factory=list) # Replaced historical_validation.lessons
    
    # Rendering cache
    rendered_pre_context_markdown: str = ""
    rendered_market_context_markdown: str = ""


class TaskInputs(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    date_anchor: Optional[str] = None
    window: ReplayWindow = Field(default_factory=ReplayWindow)
    portfolio_ops: bool = False


class PlanTask(BaseModel):
    id: str
    title: str
    description: str
    worker_type: WorkerType
    inputs: TaskInputs = Field(default_factory=TaskInputs)
    expected_output: str = "结论 + 证据 + 不确定性 + 待跟进问题"
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    confidence: Optional[float] = None
    open_questions: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    plan_id: str
    goal: str
    constraints: List[str] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)
    tasks: List[PlanTask] = Field(default_factory=list)
    turn: int = 0
    stop_reason: Optional[str] = None


class Conclusion(BaseModel):
    final_report: str
    lessons_learned: List[LessonItem] = Field(default_factory=list)
    replay_summary: Optional[str] = None
