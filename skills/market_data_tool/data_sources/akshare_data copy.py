"""
AkShare数据源
使用AkShare库获取A股行情数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .base import BaseDataSource, DataSourceError, DataSourceTimeout, SymbolNotFoundError
from ..utils.circuit_breaker import circuit_break
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AkShareDataSource(BaseDataSource):
    """AkShare数据源实现类"""

    def __init__(self, timeout: int = 15):
        """
        初始化AkShare数据源
        
        Args:
            timeout: 请求超时时间（秒）
        """
        super().__init__("akshare", timeout)

    @circuit_break("akshare")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        获取股票行情数据
        
        Args:
            symbol: 股票代码
            market: 市场类型(仅支持A-share)
            
        Returns:
            股票行情数据字典
        """
        if market != "A-share":
            raise DataSourceError(f"AkShare不支持{market}市场", self.name)

        try:
            self.logger.info(f"正在从AkShare获取 {symbol} 的实时行情")
            
            # 方案: 使用stock_zh_a_hist获取最近2天数据，取最新一条作为当前行情
            # 这种方法比stock_zh_a_spot_em轻量很多，只获取指定股票的数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - pd.Timedelta(days=2)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
            
            if df.empty:
                raise SymbolNotFoundError(symbol, self.name)
            
            # 获取最新一条数据
            latest_data = df.iloc[-1]
            
            # 解析数据
            current_price = float(latest_data['收盘'])
            open_price = float(latest_data['开盘'])
            high_price = float(latest_data['最高'])
            low_price = float(latest_data['最低'])
            previous_close = float(latest_data['收盘'])  # 当日收盘就是当前价
            
            # 如果有前一天数据，计算涨跌幅
            change_amount = 0
            change_percent = 0
            if len(df) >= 2:
                prev_close = float(df.iloc[-2]['收盘'])
                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0
                previous_close = prev_close
            
            volume = int(latest_data['成交量'])  # 单位：手
            turnover = float(latest_data['成交额'])
            stock_name = f"{symbol}"  # 暂时用代码作为名称，可以后续优化
            
            result = {
                "symbol": symbol,
                "name": stock_name,
                "current_price": current_price,
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "previous_close": previous_close,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "volume": volume,
                "turnover": turnover,
                "timestamp": datetime.now(),
                "market": market,
                "currency": "CNY",
                "status": "trading",
                "source": "akshare",
                "data_date": latest_data['日期']  # 添加数据日期
            }
            
            self.logger.info(f"成功从AkShare获取 {symbol} 数据: 当前价格 {current_price} (数据日期: {latest_data['日期']})")
            return result

        except SymbolNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"AkShare获取 {symbol} 数据失败: {str(e)}")
            raise DataSourceError(f"获取行情失败: {str(e)}", self.name)

    @circuit_break("akshare")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            market: 市场类型
            period: 时间周期 (转换AkShare支持的格式)
            interval: 时间间隔
            
        Returns:
            历史数据列表
        """
        if market != "A-share":
            return []

        try:
            self.logger.info(f"正在从AkShare获取 {symbol} 的历史数据")
            
            # 转换周期
            start_date = "20200101" # 默认较早时间，akshare会自动截取
            end_date = datetime.now().strftime("%Y%m%d")
            
            # 简单映射 period 到 start_date (粗略)
            if period == "1mo":
                start_date = (datetime.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
            elif period == "3mo":
                start_date = (datetime.now() - pd.Timedelta(days=90)).strftime("%Y%m%d")
            elif period == "1y":
                start_date = (datetime.now() - pd.Timedelta(days=365)).strftime("%Y%m%d")
                
            # 获取日线数据
            # adjust="qfq" 前复权
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df.empty:
                self.logger.warning(f"AkShare未找到 {symbol} 的历史数据")
                return []
                
            historical_data = []
            for _, row in df.iterrows():
                historical_data.append({
                    'timestamp': row['日期'], # 格式通常是 YYYY-MM-DD
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'adj_close': float(row['收盘']) # 已经是复权后的
                })
                
            # 排序
            historical_data.sort(key=lambda x: x['timestamp'])
            
            return historical_data

        except Exception as e:
            self.logger.error(f"AkShare获取历史数据失败: {str(e)}")
            return []

    def validate_symbol(self, symbol: str, market: str) -> bool:
        """验证股票代码"""
        if market != "A-share":
            return False
        # 简单验证：6位数字
        return len(symbol) == 6 and symbol.isdigit()

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 尝试获取一个指数数据来测试连接
            # 上证指数 000001
            df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20250101", end_date="20250102", adjust="qfq")
            print(df)
            return not df.empty
        except Exception as e:
            self.logger.error(f"AkShare连接测试失败: {e}")
            return False

    def get_data_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        try:
            connection_ok = self.test_connection()
            return {
                "name": self.name,
                "type": "akshare",
                "status": "connected" if connection_ok else "disconnected",
                "timeout": self.timeout,
                "last_test": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "name": self.name,
                "type": "akshare",
                "status": "error",
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }


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
    
    # 测试6: 批量获取市场数据（可选）
    print("\n6. 测试批量市场数据获取...")
    try:
        print("正在获取A股全市场实时行情（这可能需要一些时间）...")
        
        # 获取全市场数据的前10条作为样本
        import akshare as ak
        all_market_df = ak.stock_zh_a_spot_em()
        
        if not all_market_df.empty:
            sample_count = min(10, len(all_market_df))
            print(f"✅ 成功获取全市场数据，共{len(all_market_df)}只股票")
            print(f"前{sample_count}只股票样本:")
            
            for i in range(sample_count):
                row = all_market_df.iloc[i]
                print(f"  {i+1}. {row['代码']} {row['名称']}: ¥{row['最新价']:.2f} ({row['涨跌幅']:.2f}%)")
        else:
            print("⚠️ 未获取到市场数据")
            
    except Exception as e:
        print(f"❌ 获取市场数据失败: {str(e)}")
    
    print("\n=== 测试完成 ===")
    print("💡 AkShare数据源测试完成！该数据源专注于中国金融市场，数据质量高且更新及时。")


if __name__ == "__main__":
    main()
