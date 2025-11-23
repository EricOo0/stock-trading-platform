import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, PrivateAttr

from .config import Config
from .utils.rate_limiter import rate_limiter
from .utils.error_handler import create_error_response
from .utils.llm_symbol_extractor import LLMSymbolExtractor
from .services.a_share_service import AShareService
from .services.us_stock_service import USStockService
from .services.hk_stock_service import HKStockService

# 配置日志
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class MarketDataInput(BaseModel):
    query: str = Field(description="The query about stock market data, e.g., 'AAPL price', '平安银行行情', 'NVIDIA stock price'")

class MarketDataSkill(BaseTool):
    """
    市场数据获取工具的核心实现类
    提供自然语言接口和数据获取功能
    """
    name: str = "market_data_tool"
    description: str = "提供A股、美股、港股的实时行情数据获取功能，支持自然语言查询股票价格和历史数据。支持中英文公司名称和股票代码。"
    args_schema: type[BaseModel] = MarketDataInput

    _rate_limiter: Any = PrivateAttr()
    _a_share_service: AShareService = PrivateAttr()
    _us_stock_service: USStockService = PrivateAttr()
    _hk_stock_service: HKStockService = PrivateAttr()
    _llm_extractor: Optional[LLMSymbolExtractor] = PrivateAttr(default=None)

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """Initialize the market data skill with all required components
        
        Args:
            llm: Optional LLM instance for intelligent symbol extraction
        """
        super().__init__()
        self._rate_limiter = rate_limiter
        self._a_share_service = AShareService()
        self._us_stock_service = USStockService()
        self._hk_stock_service = HKStockService()
        
        # Initialize LLM-based symbol extractor if LLM is provided
        if llm:
            self._llm_extractor = LLMSymbolExtractor(llm)
            logger.info("AI-fundin市场数据获取工具已初始化 (使用LLM智能解析)")
        else:
            logger.info("AI-fundin市场数据获取工具已初始化 (使用正则表达式解析)")

    def _run(self, query: str) -> Dict[str, Any]:
        """
        Claude Skill的主入口函数
        处理自然语言输入并返回市场数据

        Args:
            query: 用户输入的自然语言文本

        Returns:
            包含市场行情数据的字典，或错误信息
        """
        text_input = query
        try:
            logger.info(f"收到用户查询: {text_input}")

            # 解析自然语言输入
            symbols = self._extract_symbols_from_text(text_input)

            if not symbols:
                return create_error_response(
                    symbol=text_input,
                    error_code="NO_SYMBOL_FOUND",
                    error_message="未能从输入中提取有效的股票代码",
                    suggestion="请输入正确的股票代码或股票名称，例如：000001、AAPL、00700"
                )

            # 处理批量请求
            if len(symbols) > 1:
                return self._handle_batch_request(symbols)
            else:
                return self._handle_single_request(symbols[0])

        except Exception as e:
            logger.error(f"处理用户请求时发生错误: {str(e)}")
            return create_error_response(
                symbol=text_input,
                error_code="INTERNAL_ERROR",
                error_message="系统内部错误，请稍后重试",
                suggestion="请稍后重试或联系技术支持"
            )

    async def _arun(self, query: str) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        return self._run(query)

    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """
        从自然语言文本中提取股票代码和名称
        优先使用LLM智能解析，回退到正则表达式

        Args:
            text: 用户输入的自然语言文本

        Returns:
            股票代码列表
        """
        # Try LLM-based extraction first
        if self._llm_extractor:
            try:
                symbols = self._llm_extractor.extract(text)
                if symbols:
                    logger.info(f"LLM extracted symbols: {symbols} from query: {text}")
                    return symbols[:Config.BATCH_MAX_SYMBOLS]
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, falling back to regex")
        
        # Fallback to regex-based extraction
        return self._extract_symbols_regex(text)
    
    def _extract_symbols_regex(self, text: str) -> List[str]:
        """
        使用正则表达式从文本中提取股票代码
        这是LLM提取失败时的后备方案
        
        Args:
            text: 用户输入的文本
            
        Returns:
            股票代码列表
        """
        symbols = []
        import re

        # 中文公司名称到股票代码的映射（保留常用的映射作为后备）
        chinese_company_mapping = {
            # 常用美股
            '苹果': 'AAPL', '微软': 'MSFT', '谷歌': 'GOOGL', '亚马逊': 'AMZN',
            '特斯拉': 'TSLA', '英伟达': 'NVDA', 'META': 'META',
            '阿里巴巴': 'BABA', '百度': 'BIDU', '京东': 'JD', '拼多多': 'PDD',
            
            # 常用A股
            '平安银行': '000001', '招商银行': '600036', '贵州茅台': '600519', 
            '五粮液': '000858', '中国平安': '601318', '宁德时代': '300750',
            
            # 常用港股
            '腾讯': '00700', '腾讯控股': '00700', '美团': '03690', '小米': '01810',
        }

        # 步骤1: 优先处理中文公司名称
        text_clean = text.upper()
        for company_name, symbol in chinese_company_mapping.items():
            if company_name in text:
                symbols.append(symbol)

        # 步骤2: 处理股票代码
        # Pattern 1: A股代码 (6位数字)
        matches = re.findall(r'(\d{6})', text_clean)
        symbols.extend([match for match in matches if self._is_valid_share_code(match)])

        # Pattern 2: US stock symbols (AAPL, TSLA, etc.)
        matches = re.findall(r'\b([A-Z]{1,5})\b', text_clean)
        symbols.extend([match for match in matches if self._is_valid_us_symbol(match)])

        # Pattern 3: HK stock symbols (00700, 02318, etc.)
        matches = re.findall(r'\b0\d{4}\b', text_clean)
        symbols.extend([match for match in matches if self._is_valid_hk_code(match)])

        # 步骤3: 移除重复项
        seen = set()
        unique_symbols = []
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)

        return unique_symbols[:Config.BATCH_MAX_SYMBOLS]

    def _is_valid_share_code(self, symbol: str) -> bool:
        """验证是否为有效的A股代码"""
        if len(symbol) != 6 or not symbol.isdigit():
            return False
        prefix = symbol[:3]
        return prefix in Config.A_SHARE_PREFIXES

    def _is_valid_us_symbol(self, symbol: str) -> bool:
        """验证是否为有效的美股代码"""
        import re
        return bool(re.match(r'^[A-Z]{1,5}$', symbol))

    def _is_valid_hk_code(self, symbol: str) -> bool:
        """验证是否为有效的港股代码"""
        return bool(symbol.startswith('0') and len(symbol) == 5 and symbol.isdigit())

    def get_historical_data(self, symbol: str, period: str = "30d", interval: str = "1d") -> Dict[str, Any]:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 时间间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            历史数据或错误信息
        """
        logger.info(f"获取历史数据: {symbol}, 周期: {period}, 间隔: {interval}")

        # 确定市场类型
        market = self._determine_market(symbol)

        if not market:
            return create_error_response(
                symbol=symbol,
                error_code="INVALID_SYMBOL",
                error_message=f"无法识别股票代码 {symbol} 的市场类型",
                suggestion="请检查股票代码格式：A股6位数字，美股1-5位字母，港股5位数字"
            )

        # 根据市场类型使用相应服务
        try:
            if market == "A-share":
                return self._a_share_service.get_historical_data(symbol, period, interval)
            elif market == "US":
                return self._us_stock_service.get_historical_data(symbol, period, interval)
            elif market == "HK":
                return self._hk_stock_service.get_historical_data(symbol, period, interval)
            else:
                return create_error_response(
                    symbol=symbol,
                    error_code="UNSUPPORTED_MARKET",
                    error_message=f"暂不支持{market}市场历史数据查询",
                    suggestion="目前支持A股、美股、港股市场历史数据查询"
                )
        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            return create_error_response(
                symbol=symbol,
                error_code="INTERNAL_ERROR",
                error_message=f"获取历史数据时发生错误: {str(e)}",
                suggestion="请稍后重试，或联系技术支持"
            )

    def _handle_single_request(self, symbol: str) -> Dict[str, Any]:
        """
        处理单只股票的信息获取请求

        Args:
            symbol: 股票代码

        Returns:
            股票行情数据或错误信息
        """
        logger.info(f"处理单只股票查询: {symbol}")

        # 确定市场类型
        market = self._determine_market(symbol)

        if not market:
            return create_error_response(
                symbol=symbol,
                error_code="INVALID_SYMBOL",
                error_message=f"无法识别股票代码 {symbol} 的市场类型",
                suggestion="请检查股票代码格式：A股6位数字，美股1-5位字母，港股5位数字"
            )

        # 根据市场类型使用相应服务
        if market == "A-share":
            return self._a_share_service.get_stock_quote(symbol)
        elif market == "US":
            return self._us_stock_service.get_stock_quote(symbol)
        elif market == "HK":
            return self._hk_stock_service.get_stock_quote(symbol)
        else:
            return create_error_response(
                symbol=symbol,
                error_code="UNSUPPORTED_MARKET",
                error_message=f"暂不支持{market}市场查询",
                suggestion="目前支持A股、美股、港股市场"
            )

    def _handle_batch_request(self, symbols: List[str]) -> Dict[str, Any]:
        """
        处理批量股票的信息获取请求

        Args:
            symbols: 股票代码列表

        Returns:
            股票行情数据列表或错误信息
        """
        logger.info(f"处理批量股票查询: {symbols}")

        results = []
        for symbol in symbols:
            # 支持所有市场类型
            market = self._determine_market(symbol)
            if market:
                result = self._handle_single_request(symbol)
                results.append(result)
            else:
                results.append(create_error_response(
                    symbol=symbol,
                    error_code="UNSUPPORTED_MARKET",
                    error_message=f"股票{symbol}市场类型无法识别",
                    suggestion="请检查股票代码格式：A股6位数字，美股1-5位字母，港股5位数字"
                ))

        # 汇总结果
        successful_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = len(results) - successful_count

        return {
            "status": "partial" if failed_count > 0 else "success",
            "count": len(symbols),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "symbols": symbols,
            "results": results,
            "summary": f"成功查询{successful_count}只股票，失败{failed_count}只",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _determine_market(self, symbol: str) -> Optional[str]:
        """
        根据股票代码判断所属市场

        Args:
            symbol: 股票代码

        Returns:
            市场类型或None
        """
        import re

        # A股：6位数字，指定前缀开头
        if re.match(r'^(000|001|002|300|600|601|603)\d{3}$', symbol):
            return "A-share"

        # 美股：1-5位字母
        if re.match(r'^[A-Z]{1,5}$', symbol.upper()):
            return "US"

        # 港股：5位数字，以0开头
        if re.match(r'^0\d{4}$', symbol):
            return "HK"

        return None

    def get_currency_for_market(self, market: str) -> str:
        """获取市场对应的货币"""
        currencies = {
            "A-share": "CNY",
            "US": "USD",
            "HK": "HKD"
        }
        return currencies.get(market, "CNY")

    def get_market_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service": "market_data_tool",
            "version": "1.0.0",
            "supported_markets": ["A-share", "US", "HK"],
            "features": ["single_query", "batch_query", "rate_limiting"],
            "description": "A股股票行情数据获取工具"
        }


def main_handle(text_input: str) -> Dict[str, Any]:
    """
    Claude Skill主入口函数

    Args:
        text_input: 用户输入的自然语言文本，描述希望查询的股票信息

    Returns:
        包含市场行情数据的字典

    示例:
        main_handle("获取平安银行股票行情") -> 返回平安银行的股票数据
        main_handle("查询AAPL和TSLA的价格") -> 返回苹果和特斯拉的股票数据
    """
    skill = MarketDataSkill()
    return skill._run(text_input)


if __name__ == "__main__":
    # 测试示例
    test_queries = [
        "获取000001的行情数据",
        "查询AAPL的股票价格",
        "00700现在多少钱",
        "获取平安银行、苹果、腾讯的行情",
        "这是什么股票？999999",
        "获取平安银行和苹果股票的价格",
        "比较腾讯和特斯拉的股价",
        "获取茅台招商银行的行情"
    ]

    print("AI-fundin市场数据获取工具 - 测试demo")
    print("=" * 50)

    for query in test_queries:
        print(f"查询: {query}")
        result = main_handle(query)
        print(f"提取的代码: {result.get('symbols', []) if 'symbols' in result else 'N/A'}")
        print(f"结果状态: {result.get('status', 'unknown')}")
        print("-" * 30)


if __name__ == "__main__":
    # 测试示例
    test_queries = [
        "获取000001的行情数据",
        "查询AAPL的股票价格",
        "00700现在多少钱",
        "获取平安银行、苹果、腾讯的行情",
        "这是什么股票？999999",
        "获取平安银行和苹果股票的价格",
        "比较腾讯和特斯拉的股价",
        "获取茅台招商银行的行情"
    ]

    print("AI-fundin市场数据获取工具 - 测试demo")
    print("=" * 50)

    for query in test_queries:
        print(f"查询: {query}")
        result = main_handle(query)
        print(f"提取的代码: {result.get('symbols', []) if 'symbols' in result else 'N/A'}")
        print(f"结果状态: {result.get('status', 'unknown')}")
        print("-" * 30)