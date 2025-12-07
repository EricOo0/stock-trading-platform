from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path

# Set HF Mirror for China users if not set
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

class Settings(BaseSettings):
    """系统配置类"""
    
    # === 基础配置 ===
    APP_NAME: str = "Memory System Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # === 路径配置 ===
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path(os.getcwd()) / "data")
    
    # === 存储配置 ===
    CHROMA_PERSIST_DIR: Path | None = None
    SQLITE_DB_PATH: str | None = None
    
    # === 记忆参数 ===
    # 近期记忆
    WORKING_MEMORY_MAX_ITEMS: int = 50
    WORKING_MEMORY_MAX_TOKENS: int = 8000
    
    # 中期记忆
    EPISODIC_COMPRESSION_THRESHOLD: int = 5000
    TIME_DECAY_RATE: float = 0.1
    
    # 长期记忆
    CORE_PRINCIPLES_LIMIT: int = 10
    CLUSTERING_K: int = 10
    
    # === 模型配置 ===
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1")
    
    # Embedding 配置
    EMBEDDING_PROVIDER: str = Field(default="openai", description="openai or huggingface")
    HF_EMBEDDING_MODEL: str = "BAAI/bge-large-zh"
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh"
    
    LLM_MODEL: str = "gpt-4o"
    
    # === Token 预算 ===
    TOKEN_BUDGET: dict = {
        "system_base": 800,
        "core_principles": 500,
        "working_memory": 8000,
        "episodic_memory": 2000,
        "semantic_memory": 500,
        "tools": 2000,
        "response": 4000
    }
    
    from pydantic import model_validator
    
    @model_validator(mode='after')
    def load_config_and_paths(self):
        # 1. 尝试加载 .config.yaml
        import yaml
        
        config_path = Path(".config.yaml")
        if not config_path.exists():
            # 尝试从父目录查找
            config_path = Path("..") / ".config.yaml"
            
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    
                if config:
                    # 更新 LLM 模型
                    if "model" in config:
                        self.LLM_MODEL = config["model"]
                        # 如果是 DeepSeek 或其他模型，也可以在这里更新 EMBEDDING 设置
                        
                    # 更新 API URL
                    if "api_url" in config:
                        self.OPENAI_API_BASE = config["api_url"]
                        
                    # 更新 API Key
                    if "api_keys" in config:
                        keys = config["api_keys"]
                        # 优先使用 siliconflow (如果 URL 匹配)，否则使用 openai
                        if "siliconflow" in keys and "siliconflow" in str(self.OPENAI_API_BASE):
                            self.OPENAI_API_KEY = keys["siliconflow"]
                        elif "openai" in keys:
                            self.OPENAI_API_KEY = keys["openai"]
                    
                    # 更新 Embedding 配置
                    if "embedding_provider" in config:
                        self.EMBEDDING_PROVIDER = config["embedding_provider"]
                    if "embedding_model" in config:
                         self.HF_EMBEDDING_MODEL = config["embedding_model"]

                    print(f"🔹 Loaded config from {config_path}")
            except Exception as e:
                print(f"⚠️ Failed to load .config.yaml: {e}")

        # 2. 初始化默认路径
        if self.CHROMA_PERSIST_DIR is None:
            self.CHROMA_PERSIST_DIR = self.DATA_DIR / "chroma"
        if self.SQLITE_DB_PATH is None:
            self.SQLITE_DB_PATH = f"sqlite+aiosqlite:///{self.DATA_DIR}/memory.db"
            
        # 3. 确保存储目录存在
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if self.CHROMA_PERSIST_DIR:
             self.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 单例模式
settings = Settings()
