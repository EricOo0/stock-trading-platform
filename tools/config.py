
import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Handles configuration loading from .config.yaml and environment variables.
    Priority:
    1. Environment Variables (Highest)
    2. .config.yaml in Current Working Directory
    3. .config.yaml in User Home Directory (~/.stock_trading_platform/config.yaml or ~/.config.yaml)
    4. Default values (Lowest)
    """
    
    _config: Dict[str, Any] = {}
    _loaded: bool = False

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Loads and returns the configuration dictionary."""
        if cls._loaded:
            return cls._config

        # 1. Defaults
        config = {
            "api_keys": {
                "tavily": None,
                "llama_cloud": None,
                "openai": None,
                "siliconflow": None
            },
            "database": {
                "path": "stock_data.db"
            }
        }

        # 2. Load from YAML files
        # Search paths (in ascending priority order):
        # 1. Home directory
        # 2. ~/.stock_trading_platform/
        # 3. Current working directory
        # 4. Project root (parent of tools directory)
        
        # Helper: Find project root by looking for .config.yaml in parent directories
        def find_project_root():
            """向上查找包含 .config.yaml 的目录"""
            # Use file path to find root, more robust than getcwd
            current = os.path.dirname(os.path.abspath(__file__))
            for _ in range(5):  # 最多向上查找5层
                config_path = os.path.join(current, ".config.yaml")
                if os.path.exists(config_path):
                    return config_path
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
            return None
        
        project_config = find_project_root()
        
        file_paths = [
            os.path.expanduser("~/.config.yaml"),
            os.path.expanduser("~/.stock_trading_platform/config.yaml"),
            os.path.join(os.getcwd(), ".config.yaml"),  # CWD
        ]
        
        # 添加项目根目录的配置（如果找到）
        if project_config and project_config not in file_paths:
            file_paths.append(project_config)

        for path in file_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_config = yaml.safe_load(f)
                        if file_config and isinstance(file_config, dict):
                            logger.info(f"Loading config from {path}")
                            cls._deep_update(config, file_config)
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")

        # 3. Load from Environment Variables (Override all)
        # Mapping Env Var -> Config Key
        env_mapping = {
            "TAVILY_API_KEY": ("api_keys", "tavily"),
            "LLAMA_CLOUD_API_KEY": ("api_keys", "llama_cloud"),
            "OPENAI_API_KEY": ("api_keys", "openai"),
            "SILICONFLOW_API_KEY": ("api_keys", "siliconflow"),
            "FRED_API_KEY": ("api_keys", "fred_api_key")
        }

        for env_var, keys in env_mapping.items():
            val = os.getenv(env_var)
            if val:
                # Navigate and set
                sub = config
                for k in keys[:-1]:
                    sub = sub.setdefault(k, {})
                sub[keys[-1]] = val

        cls._config = config
        cls._loaded = True
        print(file_paths,config)
        return config

    @staticmethod
    def _deep_update(source: Dict, overrides: Dict):
        """Recursive update dictionary."""
        for key, value in overrides.items():
            if isinstance(value, dict) and value:
                returned = ConfigLoader._deep_update(source.get(key, {}), value)
                source[key] = returned
            else:
                source[key] = overrides[key]
        return source

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a top-level config value."""
        if not cls._loaded: cls.load_config()
        return cls._config.get(key, default)

    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """Helper to get API key."""
        if not cls._loaded: cls.load_config()
        return cls._config.get("api_keys", {}).get(provider)

# Singleton access
config = ConfigLoader
