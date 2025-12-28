from typing import List, Dict, Any
from sklearn.cluster import KMeans
import numpy as np
from llm.client import LLMClient
from storage.vector_store import VectorStore
from utils.logger import logger
from langchain_core.messages import HumanMessage, SystemMessage

class ConceptCluster:
    """
    概念聚类器
    分析中期记忆，通过聚类提取长期原则 (Core Principles)
    """
    
    def __init__(self, user_id: str, agent_id: str):
        self.user_id = user_id
        self.agent_id = agent_id
        self.llm_client = LLMClient.get_instance()
        # 复用已有的向量存储读取数据
        self.vector_store = VectorStore(collection_name=f"episodic_{user_id}_{agent_id}")
        
    def cluster_and_abstract(self, k: int = 5) -> List[str]:
        """
        执行聚类并抽象出原则
        
        Args:
            k: 聚类簇数
            
        Returns:
            List[str]: 提取出的核心原则列表
        """
        try:
            # 1. 获取所有记忆及其嵌入
            # Chroma get() method (需要 vector store 暴露更底层接口或在此直接使用 collection)
            # 这里直接使用 collection 访问
            result = self.vector_store.collection.get(include=["embeddings", "documents"])
            
            embeddings = result.get("embeddings")
            documents = result.get("documents")
            
            # 强化空值检查，处理 numpy 数组的情况
            has_embeddings = embeddings is not None and len(embeddings) > 0
            
            if not has_embeddings or len(embeddings) < k:
                count = len(embeddings) if embeddings is not None else 0
                logger.info(f"Not enough memories to cluster (Count: {count}, K: {k})")
                return []
                
            # 2. 执行 K-Means 聚类
            X = np.array(embeddings)
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            labels = kmeans.labels_
            
            # 3. 对每个簇生成总结
            new_principles = []
            for i in range(k):
                # 获取该簇的文档
                cluster_docs = [doc for j, doc in enumerate(documents) if labels[j] == i]
                
                if not cluster_docs:
                    continue
                    
                # 只有当簇足够大时才总结 (可选)
                if len(cluster_docs) < 3: 
                    continue
                    
                summary = self._summarize_cluster(cluster_docs)
                if summary:
                    new_principles.append(summary)
                    
            logger.info(f"Generated {len(new_principles)} new principles from clustering")
            return new_principles
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return []

    def _summarize_cluster(self, docs: List[str]) -> str:
        """总结聚类簇生成原则"""
        # 限制文档数量以适应上下文
        sample_docs = docs[:10] 
        text_block = "\n- ".join(sample_docs)
        
        system_prompt = """Analyze the following related memory events.
Abstract a single, high-level core principle or rule of thumb that explains these events.
The output must be a concise statement (one sentence).
Start with "Principle:" or "Rule:".
"""
        try:
            response = self.llm_client.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=text_block)
            ])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Cluster summarization failed: {e}")
            return ""
