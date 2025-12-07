from collections import deque
from typing import List, Dict, Optional, Any, Deque
from datetime import datetime
import json
from config import settings
from utils.logger import logger
from utils.tokenizer import tokenizer

class WorkingMemory:
    """近期记忆管理器 (Working Memory)"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # 不使用 deque 的 maxlen，改为手动管理以支持回调
        self.items: Deque[Dict] = deque()
        self.max_items = settings.WORKING_MEMORY_MAX_ITEMS
        self.max_tokens = settings.WORKING_MEMORY_MAX_TOKENS
        # 回调函数，用于触发压缩
        self.compression_callback = None

    def set_compression_callback(self, callback):
        self.compression_callback = callback
        
    def add(self, memory_item: Dict[str, Any]) -> None:
        """
        添加记忆项
        
        Args:
            memory_item: 记忆内容 dict, 包含 role, content 等
        """
        # 计算 token
        content = memory_item.get("content", "")
        if isinstance(content, dict):
            # 如果 content 是对象（如 ConversationContent），转字符串计算
            text_content = json.dumps(content, ensure_ascii=False)
        else:
            text_content = str(content)
            
        tokens = tokenizer.count_tokens(text_content)
        
        # 构造内部存储结构
        internal_item = {
            "id": memory_item.get("id"),
            "timestamp": memory_item.get("timestamp") or datetime.now().isoformat(),
            "role": memory_item.get("role", "user"),
            "content": content,
            "tokens": tokens,
            "metadata": memory_item.get("metadata", {}),
            "importance": memory_item.get("importance", 0.5),
            "protected": memory_item.get("protected", False)
        }
        
        # 1. 检查 Token 限制并压缩
        self._ensure_token_limit(new_item_tokens=tokens)
        
        # 2. 检查条目数限制并压缩
        self._ensure_item_limit()

        self.items.append(internal_item)
        logger.debug(f"Added item to WorkingMemory (Agent: {self.agent_id}, Tokens: {tokens})")

    def _ensure_item_limit(self) -> None:
        """确保不超过条目数限制"""
        while len(self.items) >= self.max_items:
            removed = self.items.popleft()
            logger.debug(f"Pruned WorkingMemory item (Count limit).")
            if self.compression_callback:
                self.compression_callback([removed])
    
    def _ensure_token_limit(self, new_item_tokens: int) -> None:
        """确保添加新项后不超过 Token 限制"""
        current_tokens = self.total_tokens()
        # 注意: 此时新项还未加入，所以是 current + new > max
        while self.items and (current_tokens + new_item_tokens > self.max_tokens):
            removed = self.items.popleft()
            current_tokens -= removed["tokens"]
            logger.debug(f"Pruned WorkingMemory item (Token limit). Freed: {removed['tokens']} tokens")
            
            # 触发压缩逻辑
            if self.compression_callback:
                self.compression_callback([removed])

    def total_tokens(self) -> int:
        """计算当前总 Token 数"""
        return sum(item["tokens"] for item in self.items)
        
    def get_context(self) -> str:
        """获取格式化的上下文文本"""
        context = []
        for item in self.items:
            role = item["role"]
            content = item["content"]
            if isinstance(content, dict):
                content = content.get("message", str(content))
            context.append(f"{role}: {content}")
        return "\n".join(context)
        
    def get_details(self) -> List[Dict]:
        """获取所有记忆详情"""
        return list(self.items)

    def clear(self) -> None:
        """清空记忆"""
        self.items.clear()
