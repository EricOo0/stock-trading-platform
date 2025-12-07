import os

class LiteLlm:
    """
    Wrapper for LiteLLM models to be compatible with ADK Agent `model` parameter.
    Allows specifying provider/model string (e.g., 'openai/deepseek-ai/DeepSeek-V3.1-Terminus').
    """
    def __init__(self, model: str):
        self.model_name = model

    def __str__(self):
        return self.model_name
    
    def __repr__(self):
        return f"LiteLlm(model='{self.model_name}')"

def get_model():
    """
    Returns the configured model instance.
    """
    # Use the specific SiliconFlow model requested by the user
    # Prefix with 'openai/' as per documentation for custom OpenAI-compatible providers
    model_name = os.environ.get("AGENT_MODEL", "openai/deepseek-ai/DeepSeek-V3.1-Terminus")
    
    # Return string directly to satisfy Pydantic validation for 'model.str'
    return model_name

def configure_environment():
    """
    Configure environment variables for custom OpenAI-compatible LLM providers and tools.
    ⚠️ CRITICAL: This MUST be called BEFORE any agent imports to ensure Tools() 
    receives the correct API keys during initialization.
    
    Call this at the very beginning of main.py, before importing api.receptionist.
    """
    # ==== LLM Provider Configuration ====
    # Set OpenAI API base for SiliconFlow
    if "OPENAI_API_BASE" not in os.environ:
        os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"
    
    # Set OpenAI API key (prefer env variable if set)
    if "OPENAI_API_KEY" not in os.environ:
        api_key = os.getenv("SILICONFLOW_API_KEY", "")
        os.environ["OPENAI_API_KEY"] = api_key
    
    # ==== Tools API Keys ====
    # 从 ConfigLoader 读取配置并设置到环境变量
    # 这样 Tools 初始化时可以通过环境变量或 ConfigLoader 获取
    
    try:
        import sys
        tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        
        from tools.config import ConfigLoader
        
        # 加载配置
        config = ConfigLoader.load_config()
        api_keys = config.get("api_keys", {})
        
        # 将配置中的 API keys 设置到环境变量（如果环境变量中没有的话）
        key_mapping = {
            "TAVILY_API_KEY": "tavily",
            "LLAMA_CLOUD_API_KEY": "llama_cloud",
            "SERPAPI_API_KEY": "serpapi",
        }
        
        for env_key, config_key in key_mapping.items():
            if env_key not in os.environ:
                value = api_keys.get(config_key)
                if value and value != "NONE":  # 跳过占位符
                    os.environ[env_key] = value
                    
    except Exception as e:
        # 如果加载失败，继续运行（使用默认值）
        print(f"Warning: Failed to load API keys from config: {e}")
    
    # ==== LiteLLM Configuration ====
    # Reduce LiteLLM logging to avoid clutter
    os.environ.setdefault("LITELLM_LOG", "ERROR")


