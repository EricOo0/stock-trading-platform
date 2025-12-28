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
        self.model_name = settings.HF_EMBEDDING_MODEL if self.provider == "huggingface" else settings.EMBEDDING_MODEL
        
        try:
            logger.info(f"⏳ 正在启动 Embedding 服务 (Provider: {self.provider}, Model: {self.model_name})...")
            if self.provider == "huggingface":
                from sentence_transformers import SentenceTransformer
                logger.info(f"⏳ 正在加载本地模型 {self.model_name}，这可能需要几十秒，请稍候...")
                self.client = SentenceTransformer(self.model_name)
                logger.info(f"✅ 模型 {self.model_name} 加载成功！")
            else:
                self.client = openai.AzureOpenAI(
                    api_key=settings.OPENAI_API_KEY or "dummy",
                    api_version="2023-05-15",
                    azure_endpoint=settings.OPENAI_API_BASE
                ) if "azure" in settings.OPENAI_API_BASE else openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY or "dummy",
                    base_url=settings.OPENAI_API_BASE
                )
                logger.info(f"✅ OpenAI Embedding 客户端初始化成功！")
        except Exception as e:
            logger.warning(f"❌ 初始化 Embedding 客户端失败: {e}。将使用 Mock 服务。")
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
