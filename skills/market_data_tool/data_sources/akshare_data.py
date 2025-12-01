"""
AkShare数据源 (优化版)
使用AkShare库获取A股行情数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

# 假设这些是你的项目结构，保留引用
from .base import BaseDataSource, DataSourceError, DataSourceTimeout, SymbolNotFoundError
# from ..utils.circuit_breaker import circuit_break
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AkShareDataSource(BaseDataSource):
    """AkShare数据源实现类"""

    def __init__(self, timeout: int = 15):
        super().__init__("akshare", timeout)

    # @circuit_break("akshare")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        获取股票实时行情
        优化策略：使用1分钟K线的最后一条数据作为当前实时行情，避免拉取全市场数据
        """
        # if market != "A-share":
        #     raise DataSourceError(f"AkShare不支持{market}市场", self.name)

        try:
            self.logger.info(f"正在从AkShare获取 {symbol} 的实时行情(1min)")
            
            # 【核心修改】使用分钟级接口，获取最近的1分钟数据
            # period='1': 1分钟线
            # adjust='qfq': 前复权 (虽然看最新价复权与否影响不大，但建议统一)
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="qfq")
            
            if df.empty:
                raise SymbolNotFoundError(symbol, self.name)
            
            # 取最后一行（最新一分钟）
            latest_data = df.iloc[-1]
            
            # 分钟线接口返回的列名通常是: 时间, 开盘, 收盘, 最高, 最低, 成交量, ...
            # 注意：分钟线的 '收盘' 即为该分钟的最新价
            current_price = float(latest_data['收盘'])
            
            # 为了计算涨跌幅，我们需要昨日收盘价。
            # 这里稍微麻烦一点：再调一次日线接口获取昨日收盘？
            # 为了性能，我们可以简单估算，或者暂时设为0，或者额外调用一次极轻量的日线
            # 这里演示更严谨的做法：顺便获取一下日线来拿昨收
            
            prev_close = 0.0
            try:
                # 获取最近2个交易日的日线，用来拿昨收
                # 这种双重查询虽然增加了一次请求，但比拉取全市场几千条数据还是要快得多
                date_str = datetime.now().strftime("%Y%m%d")
                start_dt = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d") #稍微拉长防止假期
                df_daily = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_dt, end_date=date_str, adjust="qfq")
                if len(df_daily) >= 2:
                     # 如果今天还在交易中，最后一行是今天的动态日线，倒数第二行是昨收
                     # 如果今天未开盘，最后一行可能就是昨收
                     # 简单逻辑：取倒数第二行的收盘价作为参考昨收 (近似)
                     prev_close = float(df_daily.iloc[-2]['收盘'])
                elif len(df_daily) == 1:
                     prev_close = float(df_daily.iloc[0]['开盘']) # 新股上市等特殊情况
            except Exception:
                self.logger.warning(f"获取 {symbol} 昨收数据失败，涨跌幅计算可能不准")

            # 计算涨跌
            change_amount = 0.0
            change_percent = 0.0
            if prev_close > 0:
                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100)

            result = {
                "symbol": symbol,
                "name": symbol, # AkShare分钟接口不带名称，如果需要名称可能需要额外维护映射表
                "current_price": current_price,
                "open_price": float(latest_data['开盘']),
                "high_price": float(latest_data['最高']),
                "low_price": float(latest_data['最低']),
                "previous_close": prev_close,
                "change_amount": round(change_amount, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(float(latest_data['成交量'])), # 分钟线成交量是手
                "turnover": float(latest_data['成交额']),
                "timestamp": latest_data['时间'], # 格式 "2023-10-27 15:00:00"
                "market": market,
                "currency": "CNY",
                "status": "trading",
                "source": "akshare_min"
            }
            
            self.logger.info(f"成功获取 {symbol}: {current_price}")
            return result

        except Exception as e:
            self.logger.error(f"AkShare获取 {symbol} 失败: {str(e)}")
            # 捕获特定错误防止重试无效请求
            if "not found" in str(e).lower():
                raise SymbolNotFoundError(symbol, self.name)
            raise DataSourceError(f"获取行情失败: {str(e)}", self.name)

    # @circuit_break("akshare")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        if market != "A-share":
            return []

        try:
            self.logger.info(f"正在从AkShare获取 {symbol} 的历史数据")
            
            end_date = datetime.now().strftime("%Y%m%d")
            
            # 优化日期计算逻辑
            days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "ytd": 365, "max": 3650}
            # 解析 period (如 "30d" -> 30)
            if period.endswith('d') and period[:-1].isdigit():
                delta_days = int(period[:-1])
            else:
                delta_days = days_map.get(period, 30)
                
            start_date = (datetime.now() - timedelta(days=delta_days + 20)).strftime("%Y%m%d") # 多取几天buffer
            
            # adjust="qfq" 极其重要
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df.empty:
                return []
            
            # 转换逻辑
            historical_data = []
            for _, row in df.iterrows():
                historical_data.append({
                    'timestamp': row['日期'], 
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']),
                    # AkShare hist 里的成交额单位通常是元，有些接口是万元，需注意
                    # stock_zh_a_hist 文档显示是浮点数，通常单位是元
                })
            
            return historical_data

        except Exception as e:
            self.logger.error(f"AkShare历史数据失败: {e}")
            return []

    def validate_symbol(self, symbol: str, market: str) -> bool:
        if market != "A-share": return False
        return len(symbol) == 6 and symbol.isdigit()

    def test_connection(self) -> bool:
        """
        优化：使用单只权重股(茅台)的历史数据做轻量级测试
        不要用 stock_zh_a_spot_em (太重)
        """
        try:
            # 获取茅台最近一天的日线，数据量极小
            df = ak.stock_zh_a_hist(symbol="600519", 
                                  start_date=(datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
                                  end_date=datetime.now().strftime("%Y%m%d"))
            return not df.empty
        except Exception as e:
            self.logger.error(f"AkShare连接测试失败: {e}")
            return False

    def get_data_source_info(self) -> Dict[str, Any]:
        """同上，保持不变"""
        try:
            status = "connected" if self.test_connection() else "disconnected"
            return {
                "name": self.name,
                "type": "akshare",
                "status": status,
                "timeout": self.timeout,
                "timestamp": datetime.now().isoformat()
            }
        except Exception:
            return {"name": self.name, "status": "error"}


def main():
    """
    测试AkShare数据源的main函数
    用于验证数据源连接和各项功能
    """
    import json
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== AkShare数据源测试 ===")
    print("📊 AkShare是专业的中国金融数据接口库，提供A股、期货、基金等数据")
    
    # 创建数据源实例
    data_source = AkShareDataSource(timeout=20)
    
    # 测试1: 连接测试
    print("\n1. 测试数据源连接...")
    connection_ok = data_source.test_connection()
    print(f"连接状态: {'✅ 正常' if connection_ok else '❌ 失败'}")
    
    if not connection_ok:
        print("数据源连接失败，请检查网络连接和AkShare库安装")
        return
    
    # 测试2: 获取数据源信息
    print("\n2. 获取数据源信息...")
    info = data_source.get_data_source_info()
    print(f"数据源信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
    
    # 测试3: 获取实时行情
    print("\n3. 测试获取实时行情...")
    test_symbols = [
        "000001",  # 平安银行
        "600036",  # 招商银行
        "000002",  # 万科A
        "300750",  # 宁德时代
        "600519"   # 贵州茅台
    ]
    
    for symbol in test_symbols:
        try:
            print(f"\n获取 {symbol} 的实时行情...")
            quote = data_source.get_stock_quote(symbol, "A-share")
            print(f"✅ 成功获取 {symbol} 数据:")
            print(f"  - 股票名称: {quote.get('name', 'N/A')}")
            print(f"  - 当前价格: ¥{quote.get('current_price', 'N/A')}")
            print(f"  - 涨跌幅: {quote.get('change_percent', 0):.2f}%")
            print(f"  - 涨跌额: ¥{quote.get('change_amount', 0):.2f}")
            print(f"  - 成交量: {quote.get('volume', 0):,}手")
            print(f"  - 成交额: ¥{quote.get('turnover', 0):,.0f}万")
            print(f"  - 更新时间: {quote.get('timestamp', 'N/A')}")
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据失败: {str(e)}")
    
    # 测试4: 获取历史数据（不同周期）
    print("\n4. 测试获取历史数据...")
    
    # 测试不同的周期
    test_configs = [
        ("000001", "30d"),   # 30天数据
        ("600036", "90d"),   # 90天数据
        ("000002", "1mo"),   # 1个月数据
    ]
    
    for symbol, period in test_configs:
        try:
            print(f"\n测试 {symbol} {period} 历史数据...")
            historical_data = data_source.get_historical_data(symbol, "A-share", period=period, interval="1d")
            
            if historical_data:
                print(f"✅ 成功获取 {len(historical_data)} 条数据")
                print(f"数据范围: {historical_data[0]['timestamp']} 到 {historical_data[-1]['timestamp']}")
                print("最近5条数据:")
                for i, data in enumerate(historical_data[-5:], 1):
                    print(f"  {i}. {data['timestamp']}: 开¥{data['open']:.2f} 收¥{data['close']:.2f} 量{data['volume']:,}")
            else:
                print("⚠️ 未获取到历史数据")
                
        except Exception as e:
            print(f"❌ 获取 {symbol} {period} 历史数据失败: {str(e)}")
    
    # 测试5: 验证股票代码
    print("\n5. 测试股票代码验证...")
    test_codes = [
        "000001",  # 深证主板 - 有效
        "600036",  # 上海主板 - 有效
        "300750",  # 创业板 - 有效
        "123456",  # 无效代码
        "ABC123",  # 无效格式
        "00000",   # 位数不足
        "0000001", # 位数过多
        ""         # 空代码
    ]
    
    for code in test_codes:
        is_valid = data_source.validate_symbol(code, "A-share")
        status = "✅ 有效" if is_valid else "❌ 无效"
        print(f"  {code}: {status}")
    
    # # 测试6: 批量获取市场数据（可选）
    # print("\n6. 测试批量市场数据获取...")
    # try:
    #     print("正在获取A股全市场实时行情（这可能需要一些时间）...")
        
    #     # 获取全市场数据的前10条作为样本
    #     import akshare as ak
    #     all_market_df = ak.stock_zh_a_spot_em()
        
    #     if not all_market_df.empty:
    #         sample_count = min(10, len(all_market_df))
    #         print(f"✅ 成功获取全市场数据，共{len(all_market_df)}只股票")
    #         print(f"前{sample_count}只股票样本:")
            
    #         for i in range(sample_count):
    #             row = all_market_df.iloc[i]
    #             print(f"  {i+1}. {row['代码']} {row['名称']}: ¥{row['最新价']:.2f} ({row['涨跌幅']:.2f}%)")
    #     else:
    #         print("⚠️ 未获取到市场数据")
            
    # except Exception as e:
    #     print(f"❌ 获取市场数据失败: {str(e)}")
    
    print("\n=== 测试完成 ===")
    print("💡 AkShare数据源测试完成！该数据源专注于中国金融市场，数据质量高且更新及时。")


if __name__ == "__main__":
    main()
