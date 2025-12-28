import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class ResearchJob(SQLModel, table=True):
    __tablename__ = "research_jobs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    query: str
    status: str = Field(default="pending")  # pending, running, paused, completed, failed
    result_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    events: List["ResearchEvent"] = Relationship(back_populates="job")
    artifacts: List["ResearchArtifact"] = Relationship(back_populates="job")


class ResearchEvent(SQLModel, table=True):
    __tablename__ = "research_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="research_jobs.id", index=True)
    type: str  # thought, tool_start, tool_end, log, artifact, user_remark
    payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    job: ResearchJob = Relationship(back_populates="events")


class ResearchArtifact(SQLModel, table=True):
    __tablename__ = "research_artifacts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="research_jobs.id", index=True)
    type: str  # chart, table, image
    data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    job: ResearchJob = Relationship(back_populates="artifacts")
