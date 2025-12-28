from collections import deque
from typing import List, Dict, Optional, Any, Deque
from datetime import datetime
import json
from config import settings
from utils.logger import logger
from utils.tokenizer import tokenizer


class WorkingMemory:
    """近期记忆管理器 (Working Memory)"""

    def __init__(self, user_id: str, agent_id: str):
        self.user_id = user_id
        self.agent_id = agent_id
        self.file_path = settings.DATA_DIR / f"working_{user_id}_{agent_id}.json"
        
        # 不使用 deque 的 maxlen，改为手动管理以支持回调
        self.items: Deque[Dict] = deque()
        self.max_items = settings.WORKING_MEMORY_MAX_ITEMS
        self.max_tokens = settings.WORKING_MEMORY_MAX_TOKENS
        # 回调函数，用于触发压缩
        self.compression_callback = None
        
        # 加载持久化数据
        self._load_from_disk()

    def _save_to_disk(self) -> None:
        """持久化短期记忆到磁盘"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(list(self.items), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save working memory: {e}")

    def _load_from_disk(self) -> None:
        """从磁盘加载短期记忆"""
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.items = deque(data)
            logger.info(f"Loaded {len(self.items)} items for WorkingMemory {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to load working memory: {e}")

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
            "metadata": {
                **memory_item.get("metadata", {}),
                "user_id": self.user_id,
                "agent_id": self.agent_id,
            },
            "importance": memory_item.get("importance", 0.5),
            "protected": memory_item.get("protected", False),
            "finalized": False, # 新增：标记是否已被结算
        }

        # 1. 检查 Token 限制并压缩
        self._ensure_token_limit(new_item_tokens=tokens)

        # 2. 检查条目数限制并压缩
        self._ensure_item_limit()

        self.items.append(internal_item)
        self._save_to_disk()
        logger.debug(
            f"Added item to WorkingMemory (User: {self.user_id}, Agent: {self.agent_id}, Tokens: {tokens})"
        )

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
            logger.debug(
                f"Pruned WorkingMemory item (Token limit). Freed: {removed['tokens']} tokens"
            )

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

    def get_unfinalized_details(self) -> List[Dict]:
        """获取尚未结算的记忆详情"""
        return [item for item in self.items if not item.get("finalized", False)]

    def mark_finalized(self) -> None:
        """将当前所有项标记为已结算"""
        for item in self.items:
            item["finalized"] = True
        self._save_to_disk()

    def clear(self, keep_last_n: int = 0) -> None:
        """
        清空记忆
        
        Args:
            keep_last_n: 保留最近的 N 条记录（热启动上下文）
        """
        if keep_last_n <= 0:
            self.items.clear()
        else:
            # 只保留最后 N 条
            while len(self.items) > keep_last_n:
                self.items.popleft()
        
        self._save_to_disk()
        logger.info(f"Cleared WorkingMemory (Kept last {keep_last_n} items)")
