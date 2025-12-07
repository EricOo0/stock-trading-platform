import sys
import os
# 添加当前目录到 Path
sys.path.append(os.getcwd())

from memory_system.config import settings

def verify_yaml_loading():
    print("🚀 Verifying YAML Configuration Loading...")
    print(f"Model: {settings.LLM_MODEL}")
    print(f"API Base: {settings.OPENAI_API_BASE}")
    masked_key = settings.OPENAI_API_KEY[:5] + "..." if settings.OPENAI_API_KEY else "None"
    print(f"API Key: {masked_key}")
    
    # 检查是否加载了 .config.yaml 中的值 (假设用户有 .config.yaml)
    # 这里我们只打印，由用户确认
    
if __name__ == "__main__":
    verify_yaml_loading()
