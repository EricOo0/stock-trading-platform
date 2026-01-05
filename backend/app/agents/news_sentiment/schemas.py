from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import time

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AgentType(str, Enum):
    MASTER = "master"
    WORKER = "worker"

class NewsTask(BaseModel):
    id: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Short title of the task")
    description: str = Field(..., description="Detailed description of what needs to be done")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    agent_type: AgentType = Field(default=AgentType.WORKER, description="Type of agent assigned to this task")
    result: Optional[str] = Field(None, description="The outcome or finding of the task")
    
    # Optional: If we want hierarchical tasks later
    # sub_tasks: List["NewsTask"] = Field(default_factory=list) 

class NewsPlan(BaseModel):
    tasks: List[NewsTask] = Field(default_factory=list, description="List of tasks in the plan")
    
    def get_task(self, task_id: str) -> Optional[NewsTask]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

class SentimentResult(BaseModel):
    ticker: str
    sentiment: str
    trend: Literal["up", "down", "neutral"]
    title: str
    summary: str

class EventType(str, Enum):
    PLAN_UPDATE = "plan_update"
    TASK_UPDATE = "task_update"
    CONCLUSION = "conclusion"
    ERROR = "error"

class TaskUpdateType(str, Enum):
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    OUTPUT = "output" # Final output of a task

class TaskUpdatePayload(BaseModel):
    task_id: str
    type: TaskUpdateType
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))

# For type hinting consistency in callbacks
class AgentEvent(BaseModel):
    type: EventType
    payload: Any
