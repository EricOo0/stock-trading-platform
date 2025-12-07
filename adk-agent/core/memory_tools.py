"""
Memory tools for ADK agents to access the Memory System.
Implements ReAct-style memory retrieval where agents actively decide when to query memory.
"""
from typing import Dict, Any
import requests

# Base URL for memory system
MEMORY_BASE_URL = "http://localhost:10000/api/v1"

def search_memory(query: str, agent_id: str = "default") -> str:
    """
    搜索记忆系统，查找与查询相关的历史信息、核心原则和过往对话。
    
    使用场景：
    - 需要回忆用户的偏好或历史决策
    - 需要参考过去的分析结论
    - 需要查看核心投资原则
    
    Args:
        query: 搜索查询，描述你想回忆什么信息
        agent_id: Agent ID (通常自动设置)
        
    Returns:
        相关的记忆内容，包括核心原则、历史事件和对话记录
    """
    try:
        response = requests.post(
            f"{MEMORY_BASE_URL}/memory/context",
            json={"agent_id": agent_id, "query": query},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        # Format the context for the agent
        context = data.get("context", {})
        result_parts = []
        
        if context.get("core_principles"):
            result_parts.append(f"📋 核心原则：\n{context['core_principles']}")
        
        if context.get("episodic_memory"):
            result_parts.append("\n📚 相关历史事件：")
            for item in context["episodic_memory"][:5]:
                content = item.get("content", "")
                if isinstance(content, dict):
                    content = f"{content.get('summary', '')} - {content.get('key_findings', '')}"
                result_parts.append(f"  • {content}")
        
        if context.get("working_memory"):
            result_parts.append("\n💬 近期对话：")
            for item in context["working_memory"][-5:]:
                role = item.get("role", "unknown")
                content = item.get("content", "")
                result_parts.append(f"  [{role}]: {content}")
        
        if not result_parts:
            return "未找到相关记忆。"
        
        return "\n".join(result_parts)
        
    except Exception as e:
        return f"记忆检索失败：{str(e)}"


def save_important_fact(fact: str, importance: str = "medium", agent_id: str = "default") -> str:
    """
    保存重要信息到长期记忆。
    
    使用场景：
    - 用户明确表达了重要偏好或原则
    - 发现了重要的市场规律或投资策略
    - 需要记住的关键决策或教训
    
    Args:
        fact: 要保存的重要事实或原则
        importance: 重要程度 (low/medium/high)
        agent_id: Agent ID (通常自动设置)
        
    Returns:
        保存结果确认
    """
    try:
        importance_map = {"low": 0.3, "medium": 0.5, "high": 0.8}
        importance_score = importance_map.get(importance, 0.5)
        
        response = requests.post(
            f"{MEMORY_BASE_URL}/memory/add",
            json={
                "agent_id": agent_id,
                "content": fact,
                "metadata": {
                    "role": "agent",
                    "type": "important_fact",
                    "importance": importance_score
                }
            },
            timeout=5
        )
        response.raise_for_status()
        return f"✅ 已保存重要信息：{fact[:50]}..."
        
    except Exception as e:
        return f"保存失败：{str(e)}"


def create_memory_tools_for_agent(agent_id: str):
    """
    Create memory tool functions bound to a specific agent_id.
    Returns a list of tool functions that can be passed to create_agent().
    """
    def bound_search_memory(query: str) -> str:
        return search_memory(query, agent_id=agent_id)
    
    def bound_save_important_fact(fact: str, importance: str = "medium") -> str:
        return save_important_fact(fact, importance, agent_id=agent_id)
    
    # Copy docstrings
    bound_search_memory.__doc__ = search_memory.__doc__
    bound_save_important_fact.__doc__ = save_important_fact.__doc__
    
    # Set function names for ADK
    bound_search_memory.__name__ = "search_memory"
    bound_save_important_fact.__name__ = "save_important_fact"
    
    return [bound_search_memory, bound_save_important_fact]
