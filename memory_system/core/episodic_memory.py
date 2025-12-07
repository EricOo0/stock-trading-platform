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
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # 初始化存储
        self.vector_store = VectorStore(collection_name=f"episodic_{agent_id}")
        self.graph_store = GraphStore(graph_file=f"graph_{agent_id}.json")
        
    def add_event(self, event_type: str, content: Dict, entities: List[str] = None, relations: List = None, importance: float = 0.5) -> str:
        """
        添加事件记忆
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # 1. 存入向量库 (用于语义检索)
        # 将结构化内容转换为文本描述用于嵌入
        text_content = f"{event_type}: {str(content)}"
        
        metadata = {
            "agent_id": self.agent_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "importance": importance,
            "type": "episodic"
        }
        
        self.vector_store.add(
            documents=[text_content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        # 2. 存入图数据库 (用于关系检索)
        if entities or relations:
            self.graph_store.add_event(
                event_id=memory_id,
                entities=entities or [],
                relations=relations or [],
                timestamp=timestamp,
                weight=importance
            )
            
        logger.debug(f"Added EpisodicMemory event (ID: {memory_id}, Type: {event_type})")
        return memory_id
        
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索中期记忆
        """
        # 1. 向量检索
        results = self.vector_store.query(
            query_text=query,
            n_results=top_k * 2  # 多检索一些用于后续过滤
        )
        
        # 格式化检索结果
        memories = []
        if results['ids'] and len(results['ids']) > 0 and len(results['ids'][0]) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                # 简单计算分数 (1 - distance)
                score = 1.0 - distance
                
                memories.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "score": score
                })
        
        # TODO: 结合图检索扩展相关实体
        # ...
        
        # 按分数排序并返回 top_k
        memories.sort(key=lambda x: x["score"], reverse=True)
        return memories[:top_k]
