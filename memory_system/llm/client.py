from typing import Optional, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from config import settings
from utils.logger import logger

class LLMClient:
    """
    LLM 客户端包装器 (Singleton)
    统一管理 LangChain ChatOpenAI 实例
    """
    _instance: Optional['LLMClient'] = None
    
    def __init__(self):
        if LLMClient._instance is not None:
             raise Exception("This class is a singleton!")
        
        self._llm = self._init_llm()
        LLMClient._instance = self
    
    @classmethod
    def get_instance(cls) -> 'LLMClient':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _init_llm(self) -> ChatOpenAI:
        try:
            # 同样支持从 settings 加载配置
            # 注意: LangChain 的 openai_api_base 是 base_url
            llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE,
                temperature=0.3, # 记忆任务通常需要较低的温度以保持准确性
                max_tokens=2000
            )
            logger.info(f"LLM Client initialized with model: {settings.LLM_MODEL}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM Client: {e}")
            raise

    def invoke(self, messages: List[BaseMessage], **kwargs) -> Any:
        """调用 LLM"""
        try:
            return self._llm.invoke(messages, **kwargs)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

    def get_llm(self) -> ChatOpenAI:
        """获取原始 LangChain LLM 实例 (用于 Chain)"""
        return self._llm

# 预实例化（可选，也可以懒加载）
# llm_client = LLMClient.get_instance()
