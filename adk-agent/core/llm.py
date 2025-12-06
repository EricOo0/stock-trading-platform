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
