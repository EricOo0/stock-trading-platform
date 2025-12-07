import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional, Any
from config import settings
from utils.logger import logger
from utils.embeddings import embedding_service

class VectorStore:
    """向量存储包装类 (ChromaDB)"""
    
    def __init__(self, collection_name: str = "episodic_memory"):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
        """
        try:
            self.client = chromadb.PersistentClient(
                path=str(settings.CHROMA_PERSIST_DIR),
                settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"VectorStore initialized (Collection: {collection_name})")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """
        添加文档到向量库
        """
        try:
            # 如果没有提供嵌入，自动生成
            if embeddings is None:
                embeddings = embedding_service.embed_documents(documents)
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            logger.debug(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        查询向量库
        """
        try:
            query_embedding = embedding_service.embed_query(query_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            raise

    def delete(self, ids: List[str]) -> None:
        """删除文档"""
        try:
            self.collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
            
    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()
