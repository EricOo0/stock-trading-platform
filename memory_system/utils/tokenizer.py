import tiktoken
from .logger import logger

class Tokenizer:
    """Token计数工具"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except Exception:
            # Fallback to cl100k_base which is used by gpt-4
            self.encoder = tiktoken.get_encoding("cl100k_base")
            
    def count_tokens(self, text: str) -> int:
        """计算文本Token数"""
        if not text:
            return 0
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback approximation: 1 token ~= 4 chars (English) or 1 char (Chinese)
            # 这是一个非常粗略的估计
            return len(text)

# 单例
tokenizer = Tokenizer()
