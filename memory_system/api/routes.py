from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio
from typing import Dict, Any
from datetime import datetime
from .schemas import (
    AddMemoryRequest,
    AddMemoryResponse,
    RetrieveMemoryRequest,
    RetrieveMemoryResponse,
    GetContextRequest,
    GetContextResponse,
    GetStatsResponse,
    ErrorResponse,
    ExtractEventRequest,
    ClusterRequest,
    FinalizeSessionRequest,
    FinalizeSessionResponse,
)
from core.manager import MemoryManager
from utils.logger import logger

router = APIRouter()
manager = MemoryManager.get_instance()


@router.post("/memory/add", response_model=AddMemoryResponse)
async def add_memory(
    request: AddMemoryRequest, background_tasks: BackgroundTasks = None
):
    """
    添加记忆

    由系统自动管理 Memory Pipeline:
    1. 存入 Working Memory
    2. 溢出时 -> 压缩 & 提取 -> Episodic Memory
    3. 定期 -> 聚类 & 抽象 -> Semantic Memory
    """
    try:
        logger.info(
            f"💾 Adding memory for user: {request.user_id}, agent: {request.agent_id}, role: {request.metadata.get('role', 'user')}"
        )
        logger.debug(f"   Content preview: {str(request.content)[:100]}...")

        # 使用 to_thread 运行同步的 add_memory，因为它可能会触发耗时的压缩逻辑 (LLM 提取)
        result = await asyncio.to_thread(
            manager.add_memory,
            user_id=request.user_id,
            agent_id=request.agent_id,
            content=request.content,
            role=request.metadata.get("role", "user"),
            memory_type="conversation",
            metadata=request.metadata,
        )

        return AddMemoryResponse(**result)
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/context", response_model=GetContextResponse)
async def get_context(request: GetContextRequest):
    """获取完整上下文"""
    try:
        logger.info(
            f"🔍 Getde s sting context for user: {request.user_id}, agent: {request.agent_id}"
        )
        logger.debug(
            f"   Query: {request.query[:100]}..."
            if len(request.query) > 100
            else f"   Query: {request.query}"
        )
        # 向量检索和图搜索是 I/O 密集型操作，使用 to_thread 避免阻塞事件循环
        context_data = await asyncio.to_thread(
            manager.get_context,
            user_id=request.user_id,
            agent_id=request.agent_id,
            query=request.query,
            session_id=request.session_id,
        )

        # 构造响应
        processed_context = {
            "system_prompt": "",
            "core_principles": context_data["core_principles"],
            "user_persona": context_data.get("user_persona"),
            "working_memory": context_data["working_memory"],
            "episodic_memory": context_data["episodic_memory"],
            "semantic_memory": [{"content": str(context_data["semantic_memory"])}],
        }

        # 使用真实 token 统计
        token_usage = context_data.get("token_usage", {})

        return GetContextResponse(
            status="success", context=processed_context, token_usage=token_usage
        )
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/finalize", response_model=FinalizeSessionResponse)
async def finalize_session(request: FinalizeSessionRequest):
    """结算会话：异步提取并沉淀记忆"""
    try:
        logger.info(f"🏁 Finalizing session for user: {request.user_id}")
        result = manager.finalize_session(
            user_id=request.user_id, agent_id=request.agent_id
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
        return FinalizeSessionResponse(
            status=result["status"],
            task_id=result.get("task_id"),
            processed_items=0,  # 异步任务，初始处理数为0
            timestamp=datetime.now(),
            message=f"Task queued with ID: {result.get('task_id')}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/task/{task_id}")
async def get_task_status(task_id: str):
    """获取异步任务状态"""
    status = manager.get_task_status(task_id)
    return {"task_id": task_id, "data": status}


@router.get("/memory/stats", response_model=GetStatsResponse)
async def get_stats(user_id: str, agent_id: str):
    """获取统计信息"""
    try:
        stats = manager.get_stats(user_id, agent_id)
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
