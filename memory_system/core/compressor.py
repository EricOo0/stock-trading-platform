from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from llm.client import LLMClient
from config import settings
from utils.logger import logger

class MemoryCompressor:
    """
    记忆压缩器
    负责将近期记忆（对话历史）压缩为中期记忆（摘要/事件）
    """
    
    def __init__(self):
        self.llm_client = LLMClient.get_instance()
        
    def summarize_conversation(self, messages: List[Dict]) -> str:
        """
        总结对话片段
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            
        Returns:
            str: 总结文本
        """
        if not messages:
            return ""
            
        # 构造 prompt
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        system_prompt = """You are a helpful assistant that summaries conversation history.
Please summarize the following conversation into a concise paragraph. 
Focus on key facts, decisions, and user preferences.
Ignore trivial chitchat.
Target length: 50-100 words.
"""
        
        try:
            response = self.llm_client.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=conversation_text)
            ])
            summary = response.content
            logger.debug(f"Compressed {len(messages)} messages into summary: {summary[:50]}...")
            return summary
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return "Failed to generate summary." # Fallback

# 单例
compressor = MemoryCompressor()
