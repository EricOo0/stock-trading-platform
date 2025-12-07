from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from .schemas import (
    AddMemoryRequest, AddMemoryResponse,
    RetrieveMemoryRequest, RetrieveMemoryResponse,
    GetContextRequest, GetContextResponse,
    GetStatsResponse, ErrorResponse,
    ExtractEventRequest, ClusterRequest
)
from core.manager import MemoryManager
from utils.logger import logger

router = APIRouter()
manager = MemoryManager.get_instance()

@router.post("/memory/add", response_model=AddMemoryResponse)
async def add_memory(request: AddMemoryRequest, background_tasks: BackgroundTasks = None):
    """
    添加记忆
    
    由系统自动管理 Memory Pipeline:
    1. 存入 Working Memory
    2. 溢出时 -> 压缩 & 提取 -> Episodic Memory
    3. 定期 -> 聚类 & 抽象 -> Semantic Memory
    """
    try:
        # 强制使用 pipeline 模式：所有输入默认为 conversation (Working Memory)
        # 系统会自动进行 Working -> Episodic -> Semantic 的流转
        
        result = manager.add_memory(
            agent_id=request.agent_id,
            content=request.content,
            role=request.metadata.get("role", "user"), # 从 metadata 获取 role
            memory_type="conversation",
            metadata=request.metadata
        )
        
        # 这里的 background_tasks 可以用于未来的显式异步任务，目前 logic 内置了
        if background_tasks:
            pass 

        return AddMemoryResponse(**result, status="success")
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/context", response_model=GetContextResponse)
async def get_context(request: GetContextRequest):
    """获取完整上下文"""
    try:
        context_data = manager.get_context(
            agent_id=request.agent_id,
            query=request.query,
            session_id=request.session_id
        )
        
        # 构造响应
        # 注意：这里需要适配 ContextData 的结构
        # Manager 返回的是 dict，需要转换为 Schema 格式
        
        processed_context = {
            "system_prompt": "", # 预留
            "core_principles": context_data["core_principles"],
            "working_memory": context_data["working_memory"],
            "episodic_memory": context_data["episodic_memory"],
            "semantic_memory": [{"content": context_data["semantic_memory"]}] # 简化适配
        }
        
        # 使用真实 token 统计
        token_usage = context_data.get("token_usage", {})
        
        return GetContextResponse(
            status="success",
            context=processed_context,
            token_usage=token_usage
        )
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats", response_model=GetStatsResponse)
async def get_stats(agent_id: str):
    """获取统计信息"""
    try:
        stats = manager.get_stats(agent_id)
        return GetStatsResponse(status="success", stats=stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Internal/Debug endpoints (Optional, can be removed or moved to admin router)
# @router.post("/memory/event/extract")
# async def extract_event(request: ExtractEventRequest):
#     ...

# @router.post("/memory/cluster")
# async def trigger_cluster(request: ClusterRequest):
#     ...
