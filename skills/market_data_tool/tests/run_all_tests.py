"""
运行所有测试套件的综合测试运行器
"""

import pytest
import sys
import traceback
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests():
    """运行所有测试套件"""

    print("=" * 80)
    print("市场数据工具 Phase 2 基础设施测试套件")
    print("=" * 80)
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 定义要运行的测试套件
    test_modules = [
        "skills.market_data_tool.tests.test_error_handler",
        "skills.market_data_tool.tests.test_config",
        "skills.market_data_tool.tests.test_rate_limiter",
        "skills.market_data_tool.tests.test_circuit_breaker",
        "skills.market_data_tool.tests.test_data_sources_base"
    ]

    results = {}
    total_tests = 0
    total_passed = 0
    total_failed = 0

    for i, test_module in enumerate(test_modules, 1):
        print(f"[{i}/{len(test_modules)}] 运行测试: {test_module.replace('skills.market_data_tool.tests.', '')}")
        print("-" * 60)

        try:
            # 运行测试模块
            result = pytest.main([
                test_module,
                '-v',  # 详细输出
                '--tb=short',  # 简短Traceback
                '--no-header',  # 无头部信息
                '--no-summary',  # 无总结
                '-rN',  # 无详细报告
            ])

            # pytest.main返回0表示全部通过
            if result == 0:
                passed = True
                failed_count = 0
                passed_count = "全部"  # 我们不知道具体数量，用"全部"表示
            else:
                passed = False
                failed_count = "部分"  # 我们不知道具体失败数量
                passed_count = "部分"

            results[test_module] = {
                'status': 'PASSED' if passed else 'FAILED',
                'passed': passed,
                'details': f'{failed_count}失败' if not passed else '全部通过'
            }

            if passed:
                total_passed += 1
                logger.info(f"✅ {test_module} - 通过")
            else:
                total_failed += 1
                logger.warning(f"❌ {test_module} - 失败")

            print()

        except Exception as e:
            results[test_module] = {
                'status': 'ERROR',
                'passed': False,
                'details': f'运行错误: {str(e)}'
            }
            total_failed += 1
            logger.error(f"🚨 {test_module} - 运行错误: {e}")
            print()

    # 打印最终总结
    print("=" * 80)
    print("测试结果总结")
    print("=" * 80)

    for module, result in results.items():
        module_name = module.replace('skills.market_data_tool.tests.', '')
        status_symbol = "✅" if result['passed'] else "❌"
        print(f"{status_symbol} {module_name:<25} {result['status']:<10} {result['details']}")

    print()
    print(f"总测试模块数: {len(test_modules)}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    print(f"成功率: {(total_passed/len(test_modules)*100):.1f}%")

    # 详细分析失败的测试
    if total_failed > 0:
        print()
        print("🚨 详细失败分析:")
        print("-" * 40)

        failed_modules = [m for m, r in results.items() if r['status'] == 'FAILED']
        error_modules = [m for m, r in results.items() if r['status'] == 'ERROR']

        if failed_modules:
            print("❌ 测试失败的模块:")
            for module in failed_modules:
                print(f"  - {module.replace('skills.market_data_tool.tests.', '')}")

        if error_modules:
            print("🚨 运行错误的模块:")
            for module in error_modules:
                print(f"  - {module.replace('skills.market_data_tool.tests.', '')}")

    print()
    print("=" * 80)

    # 生成建议
    generate_recommendations(results)

    return total_failed == 0

def generate_recommendations(results):
    """生成基于测试结果的建议"""
    print("💡 基于测试结果的建议:")
    print("-" * 40)

    failed_modules = [m for m, r in results.items() if not r['passed']]

    if not failed_modules:
        print("✅ 所有测试都通过了！基础设施看起来非常健壮，可以继续进行Phase 3的开发。")
        print("   建议：")
        print("   - 运行集成测试验证各组件间的交互")
        print("   - 考虑添加性能测试以验证系统在高负载下的表现")
        print("   - 为生产环境准备好监控和告警机制")
    else:
        if 'test_error_handler' in str(failed_modules):
            print("⚠️  错误处理系统存在问题，建议：")
            print("   - 检查错误类型的定义和继承关系")
            print("   - 验证错误响应格式的一致性")
            print("   - 确保错误边界装饰器正确捕获所有异常")

        if 'test_config' in str(failed_modules):
            print("⚠️  配置系统存在问题，建议：")
            print("   - 验证环境变量的读取和类型转换")
            print("   - 检查股票代码验证逻辑的正确性")
            print("   - 确保配置默认值的合理性")

        if 'test_rate_limiter' in str(failed_modules):
            print("⚠️  限流系统存在问题，建议：")
            print("   - 验证令牌桶算法的实现")
            print("   - 检查内存管理和过期清理机制")
            print("   - 确保线程安全性实现正确")

        if 'test_circuit_breaker' in str(failed_modules):
            print("⚠️  熔断器系统存在问题，建议：")
            print("   - 验证熔断状态转换逻辑")
            print("   - 检查半开状态下的成功/失败处理")
            print("   - 确保并发访问时的线程安全")

        if 'test_data_sources_base' in str(failed_modules):
            print("⚠️  数据源基类存在问题，建议：")
            print("   - 验证抽象方法的定义和实现")
            print("   - 检查市场自动检测逻辑")
            print("   - 确保超时机制和错误处理正确")

    print()
    print("📋 在继续Phase 3之前，请确保:")
    print("   1. 所有失败的测试都已修复或理解了失败原因")
    print("   2. 核心功能都能按预期工作")
    print("   3. 错误处理和边界条件都已充分测试")
    print("   4. 性能满足设计要求")
    print("   5. 安全性和数据验证机制到位")

def main():
    """主函数"""
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断测试运行。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n运行测试时发生未预的错误: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()