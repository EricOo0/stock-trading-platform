
import sys
import os
import yaml

# Add parent dir to path to find tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.config import ConfigLoader

def debug_config():
    print(f"CWD: {os.getcwd()}")
    target_path = os.path.join(os.getcwd(), ".config.yaml")
    print(f"Target Config Path: {target_path}")
    print(f"Exists: {os.path.exists(target_path)}")
    
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            content = f.read()
            print("--- File Content Start ---")
            print(content)
            print("--- File Content End ---")
            try:
                parsed = yaml.safe_load(content)
                print(f"Parsed YAML: {parsed}")
            except Exception as e:
                print(f"YAML Parse Error: {e}")

    print("Loading via ConfigLoader...")
    config = ConfigLoader.load_config()
    print(f"Loaded Config: {config}")
    
    tavily_key = ConfigLoader.get_api_key("tavily")
    print(f"Tavily Key: {tavily_key}")

if __name__ == "__main__":
    debug_config()
