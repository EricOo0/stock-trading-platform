#!/usr/bin/env python3
"""
演示情绪分析Skill的完整功能
"""
import sys
from pathlib import Path
import json

skills_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skills_dir))

from sentiment_analysis_tool.skill import main_handle

def demo_sentiment_analysis():
    """演示不同股票的情绪分析"""
    
    test_cases = [
        ("分析平安银行的市场情绪", "A股 - 平安银行"),
        ("000001的情绪如何", "A股 - 代码查询"),
        ("贵州茅台的市场情绪分析", "A股 - 贵州茅台"),
        ("AAPL sentiment analysis", "美股 - 苹果"),
    ]
    
    print("=" * 80)
    print("情绪分析 Skill 功能演示")
    print("=" * 80)
    
    for query, description in test_cases:
        print(f"\n\n{'='*80}")
        print(f"📊 测试: {description}")
        print(f"查询: \"{query}\"")
        print("=" * 80)
        
        result = main_handle(query)
        
        if result['status'] == 'success':
            data = result['data']
            
            print(f"\n✅ 分析成功!")
            print(f"股票代码: {result['symbol']}")
            print(f"情绪评分: {data['score']}/100")
            print(f"情绪评级: {data['rating']}")
            print(f"分析方法: {data.get('method', 'unknown')}")
            print(f"\n📰 新闻数量: {data['news_count']} 条")
            
            print(f"\n📝 情绪摘要:")
            print(f"   {data['summary']}")
            
            print(f"\n🔑 关键驱动因素:")
            for i, driver in enumerate(data['key_drivers'][:3], 1):
                print(f"   {i}. {driver}")
            
            print(f"\n📊 情绪分解:")
            breakdown = data.get('sentiment_breakdown', {})
            print(f"   正面: {breakdown.get('positive_ratio', 0)*100:.1f}%")
            print(f"   负面: {breakdown.get('negative_ratio', 0)*100:.1f}%")
            print(f"   中性: {breakdown.get('neutral_ratio', 0)*100:.1f}%")
            
            print(f"\n📄 最新新闻 (前3条):")
            for i, news in enumerate(data['recent_news'][:3], 1):
                print(f"   {i}. {news['title']}")
                print(f"      来源: {news['source']} | 时间: {news['published_at'][:16]}")
        else:
            print(f"\n❌ 分析失败: {result.get('message', 'Unknown error')}")
    
    print("\n\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)

if __name__ == "__main__":
    demo_sentiment_analysis()
