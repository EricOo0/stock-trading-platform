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


class LessonsBlock(BaseModel):
    items: List[LessonItem] = Field(default_factory=list)


class QueryBlock(BaseModel):
    raw: str
    intent: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)


class DataProvenanceCall(BaseModel):
    tool_name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    time_range: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None


class DataProvenance(BaseModel):
    tool_calls: List[DataProvenanceCall] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class FocusBlock(BaseModel):
    priority: str = "risk_first"
    must_cover: List[str] = Field(default_factory=list)


class PreContext(BaseModel):
    version: str = "pf_pre_context/v1"
    query: QueryBlock
    memory_blocks: Dict[str, Any] = Field(default_factory=dict)
    replay: ReplayBlock = Field(default_factory=ReplayBlock)
    lessons: LessonsBlock = Field(default_factory=LessonsBlock)
    focus: FocusBlock = Field(default_factory=FocusBlock)
    open_questions: List[str] = Field(default_factory=list)
    data_provenance: DataProvenance = Field(default_factory=DataProvenance)
    rendered_markdown: str = ""


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
