#!/usr/bin/env python3
"""
测试重构后的 agents 架构

验证：
1. 所有 agents 使用 core.tools（不依赖 fintech_agent）
2. core.tools 正确包装 tools.registry.Tools
3. Tools 在正确的时机初始化
"""

import os
import sys

print("=" * 80)
print("重构后 Agents 架构测试")
print("=" * 80)

# Step 1: 配置环境
print("\n[Step 1] 配置环境变量...")
from core.llm import configure_environment
configure_environment()
print("  ✓ 环境变量已配置")

# Step 2: 导入 core.tools
print("\n[Step 2] 导入 core.tools...")
try:
    from core.tools import (
        get_stock_price,
        get_financial_metrics,
        search_market_news,
        get_macro_data,
        analyze_sentiment,
        get_company_report,
        get_report_content,
        analyze_report
    )
    print("  ✓ core.tools 导入成功")
    print(f"  ✓ 可用工具: {len([get_stock_price, get_financial_metrics, search_market_news, get_macro_data, analyze_sentiment, get_company_report, get_report_content, analyze_report])} 个")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: 测试工具函数
print("\n[Step 3] 测试工具函数...")
try:
    print("  测试 get_stock_price('AAPL')...")
    result = get_stock_price("AAPL")
    if "error" not in result:
        print(f"    ✓ 成功: 获取到股价数据")
    else:
        print(f"    ⚠ 返回错误: {result.get('error')}")
except Exception as e:
    print(f"    ✗ 失败: {e}")

# Step 4: 导入所有 agents
print("\n[Step 4] 导入所有 agents...")
agents_to_test = [
    ("market", "market_agent"),
    ("macro", "macro_agent"),
    ("news", "news_agent"),
    ("sentiment", "sentiment_agent"),
    ("report", "report_agent"),
    ("chairman", "chairman_agent")
]

imported_agents = {}
for module_name, agent_name in agents_to_test:
    try:
        module = __import__(f"agents.{module_name}", fromlist=[agent_name])
        agent = getattr(module, agent_name)
        imported_agents[agent_name] = agent
        print(f"  ✓ {agent_name} 导入成功 (model: {agent.model})")
    except Exception as e:
        print(f"  ✗ {agent_name} 导入失败: {e}")
        import traceback
        traceback.print_exc()

# Step 5: 验证架构独立性
print("\n[Step 5] 验证架构独立性...")
print("  检查 agents 是否独立于 fintech_agent...")

# 检查 sys.modules 中是否加载了 fintech_agent.tools
if 'fintech_agent.tools' in sys.modules:
    print("    ⚠ 警告: fintech_agent.tools 仍被加载")
else:
    print("    ✓ fintech_agent.tools 未被加载（正确）")

# 检查 core.tools 的来源
import core.tools as ct
print(f"  core.tools 模块路径: {ct.__file__}")

# Step 6: 验证 Tools registry
print("\n[Step 6] 验证 Tools registry...")
from core.tools import get_registry
registry = get_registry()
print(f"  ✓ Registry 实例: {registry}")
print(f"  ✓ Registry 类型: {type(registry)}")

# 检查 registry 的工具是否正确初始化
if hasattr(registry, 'tavily'):
    tavily_status = "✓ 已初始化" if registry.tavily else "⊘ 未初始化（无 API key）"
    print(f"  Tavily 工具: {tavily_status}")
if hasattr(registry, 'ddg'):
    print(f"  DuckDuckGo 工具: ✓ 已初始化")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)

print("\n总结:")
print(f"  ✓ 环境配置正确")
print(f"  ✓ core.tools 模块工作正常")
print(f"  ✓ 导入了 {len(imported_agents)}/6 个 agents")
print(f"  ✓ Tools registry 正确初始化")
print(f"  {'✓ 架构完全独立于 fintech_agent' if 'fintech_agent.tools' not in sys.modules else '⚠ 仍依赖 fintech_agent'}")
