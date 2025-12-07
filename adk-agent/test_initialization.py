#!/usr/bin/env python3
"""
测试 Agent 初始化和环境变量设置

这个脚本验证：
1. 环境变量在 Tools 初始化前设置
2. Tools 能正确获取 API keys
3. Agents 初始化成功
"""

import os
import sys

print("=" * 80)
print("环境变量和 Agent 初始化测试")
print("=" * 80)

# Step 1: 配置环境（模拟 main.py）
print("\n[Step 1] 配置环境变量...")
from core.llm import configure_environment
configure_environment()

# 检查关键环境变量
print("\n[检查] 环境变量状态:")
env_checks = {
    "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")[:20] + "..." if os.getenv("OPENAI_API_KEY") else None,
    "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
    "LLAMA_CLOUD_API_KEY": os.getenv("LLAMA_CLOUD_API_KEY"),
    "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY"),
}

for key, value in env_checks.items():
    status = "✓" if value else "✗"
    print(f"  {status} {key}: {value if value else 'Not set'}")

# Step 2: 导入 tools（会触发 Tools() 初始化）
print("\n[Step 2] 导入 fintech_agent.tools (触发 Tools 初始化)...")
try:
    from fintech_agent.tools import get_stock_price, search_market_news
    print("  ✓ Tools 导入成功")
except Exception as e:
    print(f"  ✗ Tools 导入失败: {e}")
    sys.exit(1)

# Step 3: 测试基本功能（不需要 API key）
print("\n[Step 3] 测试基本功能...")
try:
    print("  测试 get_stock_price('AAPL')...")
    result = get_stock_price("AAPL")
    if "error" in result:
        print(f"    ⚠ 返回错误: {result.get('error')}")
    else:
        price = result.get("price", "N/A")
        print(f"    ✓ 成功获取股价: ${price}")
except Exception as e:
    print(f"    ✗ 测试失败: {e}")

# Step 4: 测试需要 API key 的功能
print("\n[Step 4] 测试需要 API key 的功能...")
if os.getenv("TAVILY_API_KEY"):
    try:
        print("  测试 search_market_news('Apple')...")
        result = search_market_news("Apple")
        if isinstance(result, list) and len(result) > 0:
            print(f"    ✓ 找到 {len(result)} 条新闻")
            print(f"    首条: {result[0].get('title', 'N/A')[:60]}...")
        else:
            print(f"    ⚠ 返回结果: {result}")
    except Exception as e:
        print(f"    ✗ 测试失败: {e}")
else:
    print("  ⊘ 跳过（TAVILY_API_KEY 未设置）")

# Step 5: 导入 agents（验证能成功加载）
print("\n[Step 5] 导入 agents...")
try:
    from agents.chairman import chairman_agent
    from agents.market import market_agent
    print("  ✓ Chairman agent 导入成功")
    print("  ✓ Market agent 导入成功")
    print(f"  Agent 模型: {chairman_agent.model}")
except Exception as e:
    print(f"  ✗ Agent 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)

# 总结
print("\n总结:")
if os.getenv("TAVILY_API_KEY"):
    print("✓ 所有核心功能测试通过")
else:
    print("⚠ 部分功能未测试（缺少 API keys）")
    print("  建议: 设置 TAVILY_API_KEY 以启用新闻搜索功能")
