from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
from config import settings
from storage.vector_store import VectorStore
from storage.graph_store import GraphStore
from utils.logger import logger
from utils.embeddings import embedding_service


class EpisodicMemory:
    """中期记忆管理器 (Episodic Memory)"""

    def __init__(self, user_id: str, agent_id: str):
        self.user_id = user_id
        self.agent_id = agent_id
        # 初始化存储，使用 user_id 和 agent_id 隔离集合
        self.vector_store = VectorStore(
            collection_name=f"episodic_{user_id}_{agent_id}"
        )
        self.graph_store = GraphStore(graph_file=f"graph_{user_id}_{agent_id}.json")

    def add_event(
        self,
        event_type: str,
        content: Dict,
        entities: List[str] = None,
        relations: List = None,
        importance: float = 0.5,
        metadata_extra: Dict = None,
    ) -> str:
        """
        添加事件记忆
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # 1. 存入向量库 (用于语义检索)
        # 将结构化内容转换为文本描述用于嵌入
        text_content = f"{event_type}: {str(content)}"

        metadata = {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "importance": importance,
            "type": "episodic",
            **(metadata_extra or {})
        }

        self.vector_store.add(
            documents=[text_content], metadatas=[metadata], ids=[memory_id]
        )

        # 2. 存入图数据库 (用于关系检索)
        if entities or relations:
            self.graph_store.add_event(
                event_id=memory_id,
                entities=entities or [],
                relations=relations or [],
                timestamp=timestamp,
                weight=importance,
            )

        logger.debug(
            f"Added EpisodicMemory event (ID: {memory_id}, User: {self.user_id}, Type: {event_type})"
        )
        return memory_id

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索中期记忆 (包含图扩展与时间衰减)
        """
        # 1. 提取查询中的潜在实体 (简单正则提取大写字母单词)
        import re
        potential_entities = re.findall(r'\b[A-Z]{2,}\b', query)
        
        # 2. 图扩展：获取相关实体并增强查询
        enhanced_query = query
        if potential_entities:
            expanded_entities = self.graph_store.get_related_entities(potential_entities)
            if expanded_entities:
                enhanced_query += " Related to: " + ", ".join(expanded_entities)
                logger.info(f"Enhanced query with graph entities: {expanded_entities}")

        # 3. 向量检索
        results = self.vector_store.query(
            query_text=enhanced_query, n_results=top_k * 3  # 获取更多候选用于时间衰减重排
        )

        # 格式化检索结果并应用时间衰减
        memories = []
        now = datetime.now()

        if results["ids"] and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                doc = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                distance = results["distances"][0][i]

                # 基础语义分数 (1 - distance)
                semantic_score = 1.0 - distance

                # 时间衰减计算
                timestamp_str = meta.get("timestamp")
                decay_factor = 1.0

                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(timestamp_str)
                        days_passed = (now - ts).days
                        # 使用 log 衰减: 1 / (1 + log(1 + days))
                        import math

                        decay_factor = 1.0 / (1.0 + math.log(1 + max(0, days_passed)))
                    except Exception as e:
                        logger.error(f"Error parsing timestamp for decay: {e}")

                final_score = semantic_score * decay_factor

                memories.append(
                    {
                        "id": doc_id,
                        "content": doc,
                        "metadata": meta,
                        "semantic_score": semantic_score,
                        "decay_factor": decay_factor,
                        "score": final_score,
                    }
                )

        # 4. 冲突检测 (如果 query 涉及特定 symbol)
        for symbol in potential_entities:
            conflicts = self.detect_conflicts(symbol)
            if conflicts:
                # 将冲突信息作为特殊记忆项注入，提醒 Agent 反思
                conflict_text = f"[Memory Reflection] Detected viewpoint changes for {symbol}: " + \
                                " -> ".join([f"{c['prev']['viewpoint']} ({c['prev']['timestamp'][:10]})" for c in conflicts])
                memories.append({
                    "id": f"conflict_{symbol}",
                    "content": conflict_text,
                    "metadata": {"type": "conflict_alert"},
                    "score": 2.0  # 极高分数确保被选中
                })

        # 按最终分数重排
        memories.sort(key=lambda x: x["score"], reverse=True)
        return memories[:top_k]

    def detect_conflicts(self, symbol: str) -> List[Dict]:
        """检测特定标的的观点冲突"""
        # 检索该标的的所有投资见解
        results = self.vector_store.query(
            query_text=f"InvestmentInsight symbol {symbol}",
            n_results=10
        )
        
        insights = []
        if results["metadatas"] and len(results["metadatas"][0]) > 0:
            for i, meta in enumerate(results["metadatas"][0]):
                if meta.get("event_type") == "InvestmentInsight" and meta.get("symbol") == symbol:
                    insights.append({
                        "viewpoint": meta.get("viewpoint"),
                        "timestamp": meta.get("timestamp"),
                    })
        
        # 按时间排序
        insights.sort(key=lambda x: x["timestamp"])
        
        conflicts = []
        for i in range(1, len(insights)):
            if insights[i]["viewpoint"] != insights[i-1]["viewpoint"]:
                conflicts.append({
                    "prev": insights[i-1],
                    "curr": insights[i]
                })
        
        return conflicts
