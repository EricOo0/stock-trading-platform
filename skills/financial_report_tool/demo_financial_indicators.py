"""
财务指标功能演示脚本
简单演示如何使用 get_financial_indicators() 方法
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from skill import FinancialReportSkill
import json

def main():
    """演示财务指标获取"""
    
    skill = FinancialReportSkill()
    
    print("=" * 80)
    print("财务指标功能演示")
    print("=" * 80)
    
    # 示例1: 获取A股财务指标
    print("\n示例1: 获取招商银行(600036)财务指标")
    print("-" * 80)
    result = skill.get_financial_indicators("600036", years=3)
    
    if result['status'] == 'success':
        indicators = result['indicators']
        print(f"\n✅ 数据源: {result['data_source']}")
        print(f"\n📊 关键指标:")
        print(f"  ROE: {indicators['shareholder_return'].get('roe', 'N/A')}%")
        print(f"  资产负债率: {indicators['debt'].get('asset_liability_ratio', 'N/A')}%")
        print(f"  毛利率: {indicators['profit'].get('gross_margin', 'N/A')}%")
        print(f"  净利率: {indicators['profit'].get('net_margin', 'N/A')}%")
    
    # 示例2: 获取美股财务指标
    print("\n\n示例2: 获取苹果(AAPL)财务指标")
    print("-" * 80)
    result = skill.get_financial_indicators("AAPL", years=3)
    
    if result['status'] == 'success':
        indicators = result['indicators']
        print(f"\n✅ 数据源: {result['data_source']}")
        print(f"\n📊 关键指标:")
        print(f"  ROE: {indicators['shareholder_return'].get('roe', 'N/A')}%")
        print(f"  自由现金流: {indicators['cashflow'].get('free_cash_flow', 'N/A')}")
        print(f"  毛利率: {indicators['profit'].get('gross_margin', 'N/A')}%")
        print(f"  营业收入YoY: {indicators['revenue'].get('revenue_yoy', 'N/A')}%")
    
    # 示例3: 使用缓存
    print("\n\n示例3: 测试缓存功能")
    print("-" * 80)
    print("第一次请求 (从API获取)...")
    result1 = skill.get_financial_indicators("600036", years=2, use_cache=True)
    print(f"  数据源: {result1.get('data_source')}")
    
    print("\n第二次请求 (从缓存获取)...")
    result2 = skill.get_financial_indicators("600036", years=2, use_cache=True)
    print(f"  数据源: {result2.get('data_source')}")
    
    print("\n" + "=" * 80)
    print("演示完成!")
    print("=" * 80)

if __name__ == "__main__":
    main()
