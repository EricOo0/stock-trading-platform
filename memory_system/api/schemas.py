# API Schemas - Pydantic Models

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型枚举"""

    WORKING = "working"  # Alias for conversation
    CONVERSATION = "conversation"  # New explicit type
    EVENT = "event"
    KNOWLEDGE = "knowledge"


class Role(str, Enum):
    """对话角色"""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class SemanticCategory(str, Enum):
    """长期记忆分类"""

    CORE_PRINCIPLE = "core_principle"
    EXPERIENCE_RULE = "experience_rule"
    USER_PREFERENCE = "user_preference"
    DOMAIN_KNOWLEDGE = "domain_knowledge"


# ==================== Request Models ====================


class ConversationContent(BaseModel):
    """对话内容"""

    role: Role
    message: str
    timestamp: Optional[datetime] = None


class ExtractEventRequest(BaseModel):
    text: str
    save: bool = True  # 是否自动保存提取结果


class ClusterRequest(BaseModel):
    k: int = 5  # 聚类数


class EventContent(BaseModel):
    """事件内容"""

    event_type: str = Field(..., description="事件类型，如 stock_analysis")
    entities: List[str] = Field(..., description="涉及的实体")
    relations: List[tuple] = Field(default_factory=list, description="三元组关系")
    key_findings: Dict = Field(default_factory=dict, description="关键发现")


class AddMemoryRequest(BaseModel):
    """添加记忆请求"""

    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(..., description="Agent ID")
    content: Any = Field(..., description="记忆内容")
    metadata: Optional[Dict] = Field(default_factory=dict, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "agent_id": "market_agent",
                "content": "Apple股票怎么样？",
                "metadata": {
                    "role": "user",
                    "session_id": "sess_123",
                    "importance": 0.8,
                },
            }
        }


class RetrieveMemoryRequest(BaseModel):
    """检索记忆请求"""

    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(..., description="Agent ID")
    query: str = Field(..., description="查询文本")
    memory_types: List[Literal["working", "episodic", "semantic"]] = Field(
        default=["episodic", "semantic"], description="要检索的记忆类型"
    )
    top_k: int = Field(default=5, ge=1, le=50, description="返回数量")
    time_range: Optional[Dict[str, datetime]] = Field(
        None, description="时间范围，格式: {start: datetime, end: datetime}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "agent_id": "market_agent",
                "query": "Apple股票分析",
                "memory_types": ["episodic", "semantic"],
                "top_k": 5,
            }
        }


class GetContextRequest(BaseModel):
    """获取上下文请求"""

    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(..., description="Agent ID")
    query: str = Field(..., description="当前查询")
    session_id: Optional[str] = Field(None, description="会话ID")
    task_type: Optional[str] = Field(None, description="任务类型，用于上下文感知检索")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "agent_id": "market_agent",
                "query": "分析Tesla股票",
                "session_id": "sess_123",
                "task_type": "stock_analysis",
            }
        }


class CompressMemoryRequest(BaseModel):
    """压缩记忆请求"""

    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(..., description="Agent ID")
    time_window_days: int = Field(
        default=30, ge=1, le=365, description="压缩时间窗口（天）"
    )
    force: bool = Field(default=False, description="是否强制压缩")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "agent_id": "market_agent",
                "time_window_days": 30,
                "force": False,
            }
        }


# ==================== Response Models ====================


class AddMemoryResponse(BaseModel):
    """添加记忆响应"""

    status: Literal["success", "error"]
    memory_id: str
    stored_in: List[str] = Field(..., description="存储位置列表")
    message: Optional[str] = None


class MemoryItem(BaseModel):
    """记忆项"""

    memory_id: str
    type: str
    content: str
    score: float = Field(..., ge=0, le=1, description="相关性分数")
    timestamp: datetime
    metadata: Optional[Dict] = None


class RetrieveMemoryResponse(BaseModel):
    """检索记忆响应"""

    status: Literal["success", "error"]
    results: List[MemoryItem]
    total_count: int
    message: Optional[str] = None


class TokenUsage(BaseModel):
    """Token使用统计"""

    core_principles: int
    working_memory: int
    episodic_memory: int
    semantic_memory: int
    total: int


class ContextData(BaseModel):
    """上下文数据"""

    system_prompt: str
    core_principles: str
    user_persona: Optional[Dict] = None # 新增：结构化用户画像
    working_memory: List[Dict]
    episodic_memory: List[Dict]
    semantic_memory: List[Dict]


class GetContextResponse(BaseModel):
    """获取上下文响应"""

    status: Literal["success", "error"]
    context: ContextData
    token_usage: TokenUsage
    message: Optional[str] = None


class CompressionStats(BaseModel):
    """压缩统计"""

    episodic_count: int = Field(..., description="压缩的中期记忆数量")
    semantic_count: int = Field(..., description="生成的长期记忆数量")
    compression_ratio: float = Field(..., description="压缩比")


class CompressMemoryResponse(BaseModel):
    """压缩记忆响应"""

    status: Literal["success", "error"]
    compressed: CompressionStats
    message: Optional[str] = None


class FinalizeSessionRequest(BaseModel):
    """结算会话请求"""

    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(..., description="Agent ID")


class FinalizeSessionResponse(BaseModel):
    """结算会话响应"""

    status: str
    task_id: Optional[str] = None # 新增：异步任务ID
    processed_items: int
    timestamp: datetime
    message: Optional[str] = None


class MemoryStats(BaseModel):
    """记忆统计"""

    working_memory: Dict = Field(..., description="近期记忆统计")
    episodic_memory: Dict = Field(..., description="中期记忆统计")
    semantic_memory: Dict = Field(..., description="长期记忆统计")


class GetStatsResponse(BaseModel):
    """获取统计响应"""

    status: Literal["success", "error"]
    stats: MemoryStats
    message: Optional[str] = None


# ==================== Error Response ====================


class ErrorResponse(BaseModel):
    """错误响应"""

    status: Literal["error"]
    error_code: str
    message: str
    details: Optional[Dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "AGENT_NOT_FOUND",
                "message": "Agent with ID 'unknown_agent' not found",
                "details": {"agent_id": "unknown_agent"},
            }
        }
