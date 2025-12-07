from typing import List, Optional
import openai
import random
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings
from utils.logger import logger

class EmbeddingService:
    """向量嵌入服务"""
    

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.is_mock = False
        
        try:
            if self.provider == "huggingface":
                from sentence_transformers import SentenceTransformer
                self.model_name = settings.HF_EMBEDDING_MODEL
                # 延迟加载，第一次调用时下载/加载模型
                self.client = SentenceTransformer(self.model_name)
                logger.info(f"Embedding Service initialized with HF model: {self.model_name}")
            else:
                self.model_name = settings.EMBEDDING_MODEL
                self.client = openai.AzureOpenAI(
                    api_key=settings.OPENAI_API_KEY or "dummy",
                    api_version="2023-05-15",
                    azure_endpoint=settings.OPENAI_API_BASE
                ) if "azure" in settings.OPENAI_API_BASE else openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY or "dummy",
                    base_url=settings.OPENAI_API_BASE
                )
                logger.info(f"Embedding Service initialized with OpenAI model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding client ({self.provider}): {e}. Using MockEmbeddingService.")
            self.is_mock = True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档嵌入
        """
        if self.is_mock:
            dims = 384 if self.provider == "huggingface" else 1536
            return [[random.random() for _ in range(dims)] for _ in texts]

        try:
            # 移除空字符串
            valid_texts = [t for t in texts if t.strip()]
            if not valid_texts:
                return []
                
            if self.provider == "huggingface":
                embeddings = self.client.encode(valid_texts)
                return embeddings.tolist()
            else:
                response = self.client.embeddings.create(
                    input=valid_texts,
                    model=self.model_name
                )
                return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            if self.is_mock: 
                 dims = 384 if self.provider == "huggingface" else 1536
                 return [[random.random() for _ in range(dims)] for _ in texts]
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_query(self, text: str) -> List[float]:
        """
        生成查询嵌入
        """
        if self.is_mock:
            dims = 384 if self.provider == "huggingface" else 1536
            return [random.random() for _ in range(dims)]

        try:
            if not text.strip():
                return []
            
            if self.provider == "huggingface":
                embedding = self.client.encode(text)
                return embedding.tolist()
            else:
                response = self.client.embeddings.create(
                    input=text,
                    model=self.model_name
                )
                return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

# 单例实例
embedding_service = EmbeddingService()
