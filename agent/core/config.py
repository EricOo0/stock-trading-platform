"""Configuration management for the Stock Analysis Agent."""

from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml
from pathlib import Path


class LLMConfig(BaseModel):
    """LLM configuration."""
    api_key: str = Field(description="OpenAI API key")
    api_base: str = Field(default="https://api.openai.com/v1", description="API base URL")
    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens to generate")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    name: str = Field(description="Server name")
    url: str = Field(description="Server URL")
    enabled: bool = Field(default=True, description="Whether the server is enabled")


class SkillsConfig(BaseModel):
    """Skills configuration."""
    path: str = Field(default="../skills/market_data_tool", description="Path to skills directory")
    enabled: bool = Field(default=True, description="Whether skills are enabled")


class AgentConfig(BaseModel):
    """Agent configuration."""
    max_iterations: int = Field(default=10, gt=0, description="Maximum agent iterations")
    verbose: bool = Field(default=True, description="Whether to enable verbose logging")


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, gt=0, lt=65536, description="Server port")
    reload: bool = Field(default=True, description="Enable auto-reload in development")


class Config(BaseModel):
    """Main configuration."""
    llm: LLMConfig
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_yaml(self, path: str = "config.yaml") -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        try:
            _config = Config.from_yaml()
        except FileNotFoundError:
            # Try example config
            _config = Config.from_yaml("config.yaml.example")
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
