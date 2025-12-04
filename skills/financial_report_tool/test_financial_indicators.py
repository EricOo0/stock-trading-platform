"""
财务指标功能测试脚本
测试 Phase 1 (AkShare A股) 和 Phase 2 (yfinance 美股/港股)
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from skill import FinancialReportSkill
import json

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_indicators(result):
    """格式化打印财务指标"""
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message')}")
        return
    
    print(f"✅ Status: {result['status']}")
    print(f"📊 Symbol: {result['symbol']}")
    print(f"🌍 Market: {result['market']}")
    print(f"📡 Data Source: {result['data_source']}")
    print(f"⏰ Timestamp: {result['timestamp']}")
    
    indicators = result.get('indicators', {})
    
    # 收入端
    print("\n📈 收入端指标:")
    revenue = indicators.get('revenue', {})
    print(f"  - 营业收入YoY: {revenue.get('revenue_yoy', 'N/A')}%")
    print(f"  - 核心营收占比: {revenue.get('core_revenue_ratio', 'N/A')}%")
    print(f"  - 现金收入比: {revenue.get('cash_to_revenue', 'N/A')}")
    
    # 利润端
    print("\n💰 利润端指标:")
    profit = indicators.get('profit', {})
    print(f"  - 扣非归母净利/每股: {profit.get('non_recurring_eps', profit.get('non_recurring_net_profit', 'N/A'))}")
    print(f"  - 经营毛利率: {profit.get('gross_margin', 'N/A')}%")
    print(f"  - 核心净利率: {profit.get('net_margin', 'N/A')}%")
    
    # 现金流
    print("\n💵 现金流指标:")
    cashflow = indicators.get('cashflow', {})
    print(f"  - 经营现金流/归母净利: {cashflow.get('ocf_to_net_profit', 'N/A')}")
    print(f"  - 自由现金流FCF: {cashflow.get('free_cash_flow', 'N/A')}")
    
    # 负债端
    print("\n📊 负债端指标:")
    debt = indicators.get('debt', {})
    print(f"  - 资产负债率: {debt.get('asset_liability_ratio', 'N/A')}%")
    print(f"  - 流动比率: {debt.get('current_ratio', 'N/A')}")
    
    # 股东回报
    print("\n🎁 股东回报指标:")
    shareholder = indicators.get('shareholder_return', {})
    print(f"  - 股息率: {shareholder.get('dividend_yield', 'N/A')}%")
    print(f"  - ROE: {shareholder.get('roe', 'N/A')}%")
    
    # 历史数据
    history = indicators.get('history', [])
    if history:
        print(f"\n📜 历史数据 (最近{len(history)}期):")
        for i, h in enumerate(history[:3], 1):
            print(f"  {i}. {h.get('date', 'N/A')}: ROE={h.get('roe', 'N/A')}%, 毛利率={h.get('gross_margin', 'N/A')}%")

def test_a_share():
    """测试A股 (AkShare)"""
    print_section("Phase 1: 测试A股财务指标 (AkShare)")
    
    skill = FinancialReportSkill()
    
    # 测试招商银行
    print("🏦 测试股票: 招商银行 (600036)")
    result = skill.get_financial_indicators("600036", years=3)
    print_indicators(result)
    
    # 测试平安银行
    print("\n" + "-" * 80 + "\n")
    print("🏦 测试股票: 平安银行 (000001)")
    result = skill.get_financial_indicators("000001", years=2)
    print_indicators(result)

def test_us_stock():
    """测试美股 (yfinance)"""
    print_section("Phase 2: 测试美股财务指标 (yfinance)")
    
    skill = FinancialReportSkill()
    
    # 测试苹果
    print("🍎 测试股票: Apple (AAPL)")
    result = skill.get_financial_indicators("AAPL", years=3)
    print_indicators(result)

def test_hk_stock():
    """测试港股 (yfinance)"""
    print_section("Phase 2: 测试港股财务指标 (yfinance)")
    
    skill = FinancialReportSkill()
    
    # 测试腾讯
    print("🎮 测试股票: 腾讯控股 (0700.HK)")
    result = skill.get_financial_indicators("0700.HK", years=3)
    print_indicators(result)

def test_cache():
    """测试缓存功能"""
    print_section("测试缓存功能")
    
    skill = FinancialReportSkill()
    
    print("第一次请求 (应该从API获取):")
    result1 = skill.get_financial_indicators("600036", years=2, use_cache=True)
    print(f"Status: {result1.get('status')}, Data Source: {result1.get('data_source')}")
    
    print("\n第二次请求 (应该从缓存获取):")
    result2 = skill.get_financial_indicators("600036", years=2, use_cache=True)
    print(f"Status: {result2.get('status')}, Data Source: {result2.get('data_source')}")
    
    print("\n禁用缓存请求:")
    result3 = skill.get_financial_indicators("600036", years=2, use_cache=False)
    print(f"Status: {result3.get('status')}, Data Source: {result3.get('data_source')}")

def test_error_handling():
    """测试错误处理"""
    print_section("测试错误处理")
    
    skill = FinancialReportSkill()
    
    print("测试无效股票代码:")
    result = skill.get_financial_indicators("INVALID123", years=3)
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message', 'N/A')}")

def main():
    """主测试函数"""
    print("\n" + "🚀" * 40)
    print("  财务指标功能测试 - Phase 1 & Phase 2")
    print("🚀" * 40)
    
    try:
        # Phase 1: A股测试
        test_a_share()
        
        # Phase 2: 美股测试
        test_us_stock()
        
        # Phase 2: 港股测试
        test_hk_stock()
        
        # 缓存测试
        test_cache()
        
        # 错误处理测试
        test_error_handling()
        
        print_section("✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
