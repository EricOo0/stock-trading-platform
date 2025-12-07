from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
from config import settings
from storage.vector_store import VectorStore
from utils.logger import logger
from utils.embeddings import embedding_service

class SemanticMemory:
    """长期记忆管理器 (Semantic Memory)"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # 长期记忆使用独立的向量集合
        self.experience_store = VectorStore(collection_name=f"semantic_exp_{agent_id}")
        self.core_principles: List[Dict] = []
        
    def add_core_principle(self, content: str, importance: float = 1.0) -> None:
        """添加核心原则 (内存存储，少量)"""
        self.core_principles.append({
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        })
        # 排序保持高优先级的在前
        self.core_principles.sort(key=lambda x: x["importance"], reverse=True)
        
        # 限制数量
        if len(self.core_principles) > settings.CORE_PRINCIPLES_LIMIT:
            self.core_principles = self.core_principles[:settings.CORE_PRINCIPLES_LIMIT]
            
    def add_experience(self, content: str, category: str, importance: float = 0.5) -> str:
        """添加经验法则 (向量存储)"""
        memory_id = str(uuid.uuid4())
        
        metadata = {
            "agent_id": self.agent_id,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            "type": "semantic"
        }
        
        self.experience_store.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        logger.debug(f"Added SemanticMemory experience (ID: {memory_id})")
        return memory_id
        
    def get_core_principles(self) -> str:
        """获取格式化的核心原则"""
        return "\n".join([f"- {p['content']}" for p in self.core_principles])
        
    def retrieve_relevant_experiences(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关经验，返回结构化数据"""
        results = self.experience_store.query(
            query_text=query,
            n_results=top_k
        )
        
        experiences = []
        if results['documents'] and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results.get('metadatas') and len(results['metadatas'][0]) > i else {}
                experiences.append({
                    "content": doc,
                    "importance": metadata.get('importance', 0.5),
                    "category": metadata.get('category', 'general')
                })
            
        return experiences
