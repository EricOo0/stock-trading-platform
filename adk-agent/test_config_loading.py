#!/usr/bin/env python3
"""
验证环境变量和配置加载流程

这个脚本展示完整的加载顺序和优先级
"""

import os
import sys

print("=" * 80)
print("环境变量加载流程详解")
print("=" * 80)

print("\n📍 Step 1: 程序启动前的状态")
print("-" * 80)
print("环境变量（来自系统）:")
for key in ["TAVILY_API_KEY", "LLAMA_CLOUD_API_KEY", "OPENAI_API_KEY"]:
    val = os.getenv(key)
    print(f"  {key}: {val if val else '❌ 未设置'}")

print("\n📍 Step 2: 调用 configure_environment()")
print("-" * 80)
from core.llm import configure_environment
configure_environment()

print("调用后的环境变量:")
for key in ["TAVILY_API_KEY", "LLAMA_CLOUD_API_KEY", "OPENAI_API_KEY", "OPENAI_API_BASE"]:
    val = os.getenv(key)
    status = "✅" if val else "❌"
    display_val = val[:30] + "..." if val and len(val) > 30 else val
    print(f"  {status} {key}: {display_val if val else '未设置'}")

print("\n📍 Step 3: ConfigLoader 加载配置")
print("-" * 80)
print("ConfigLoader 会按以下优先级加载:")
print("  1️⃣  环境变量 (最高优先级)")
print("  2️⃣  ./config.yaml (当前目录)")
print("  3️⃣  ~/.stock_trading_platform/config.yaml")
print("  4️⃣  ~/.config.yaml")
print("  5️⃣  默认值 None (最低优先级)")

# 模拟 ConfigLoader 的行为
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.config import ConfigLoader

print("\n强制重新加载配置...")
ConfigLoader._loaded = False  # 强制重新加载
config = ConfigLoader.load_config()

print("\n加载后的配置 (config['api_keys']):")
for key, val in config.get("api_keys", {}).items():
    status = "✅" if val else "❌"
    display_val = val[:30] + "..." if val and len(val) > 30 else val
    print(f"  {status} {key}: {display_val if val else 'None'}")

print("\n📍 Step 4: Tools 初始化")
print("-" * 80)
print("Tools.__init__() 会调用:")
print("  tavily_api_key = config.get_api_key('tavily')")
print("")

tavily_from_config = ConfigLoader.get_api_key("tavily")
llama_from_config = ConfigLoader.get_api_key("llama_cloud")

print(f"实际获取到的值:")
print(f"  tavily: {tavily_from_config if tavily_from_config else '❌ None'}")
print(f"  llama_cloud: {llama_from_config if llama_from_config else '❌ None'}")

print("\n" + "=" * 80)
print("💡 结论")
print("=" * 80)

if tavily_from_config:
    print("✅ Tavily API Key 已正确加载！")
    print(f"  来源: {'环境变量' if os.getenv('TAVILY_API_KEY') else '.config.yaml 文件'}")
else:
    print("❌ Tavily API Key 未设置")
    print("\n解决方案：")
    print("  方案 1: 在 .config.yaml 中设置:")
    print("    api_keys:")
    print("      tavily: 'tvly-your-key-here'")
    print("")
    print("  方案 2: 在 core/llm.py 的 configure_environment() 中设置:")
    print("    os.environ['TAVILY_API_KEY'] = 'tvly-your-key-here'")
    print("")
    print("  方案 3: 在命令行设置环境变量:")
    print("    export TAVILY_API_KEY='tvly-your-key-here'")

print("\n" + "=" * 80)
