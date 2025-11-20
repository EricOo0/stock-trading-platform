"""Basic tests for the Stock Analysis Agent."""

import pytest
from pathlib import Path

# Test configuration loading
def test_config_loading():
    """Test that configuration can be loaded."""
    from core.config import Config
    
    # Test loading from example config
    config = Config.from_yaml("config.yaml.example")
    
    assert config.llm.model == "gpt-4"
    assert config.llm.temperature == 0.7
    assert config.skills.enabled is True


# Test tool adapter
@pytest.mark.asyncio
async def test_skill_adapter():
    """Test that skill adapter can be initialized."""
    from tools.skill_adapter import SkillAdapter
    
    # This test will only pass if market_data_tool exists
    skill_path = Path("../skills/market_data_tool")
    if not skill_path.exists():
        pytest.skip("market_data_tool not found")
    
    adapter = SkillAdapter(str(skill_path))
    assert adapter.name == "market_data"
    assert "stock" in adapter.description.lower()


# Test tool manager
def test_tool_manager():
    """Test that tool manager can register tools."""
    from core.config import Config
    from tools.manager import ToolManager
    
    config = Config.from_yaml("config.yaml.example")
    manager = ToolManager(config)
    
    # Check that at least skill tool is registered if enabled
    if config.skills.enabled:
        tools = manager.get_tools()
        assert len(tools) > 0
        tool_names = manager.get_tool_names()
        assert "market_data" in tool_names


# Test memory
def test_conversation_memory():
    """Test conversation memory."""
    from core.memory import ConversationMemory
    
    memory = ConversationMemory(max_messages=5)
    
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    
    messages = memory.get_messages()
    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi there!"
    
    # Test max messages
    for i in range(10):
        memory.add_message("user", f"Message {i}")
    
    messages = memory.get_messages()
    assert len(messages) == 5  # Should only keep last 5
