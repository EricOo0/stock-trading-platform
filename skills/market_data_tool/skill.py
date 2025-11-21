import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

# 导入基础设施
from .config import Config
from .utils.rate_limiter import rate_limiter
from .utils.error_handler import create_error_response
from .services.a_share_service import AShareService
from .services.us_stock_service import USStockService
from .services.hk_stock_service import HKStockService

# 配置日志
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class MarketDataInput(BaseModel):
    query: str = Field(description="The query about stock market data, e.g., 'AAPL price', '平安银行行情'")

class MarketDataSkill(BaseTool):
    """
    市场数据获取工具的核心实现类
    提供自然语言接口和数据获取功能
    """
    name: str = "market_data_tool"
    description: str = "提供A股、美股、港股的实时行情数据获取功能，支持自然语言查询股票价格和历史数据"
    args_schema: type[BaseModel] = MarketDataInput

    _rate_limiter: Any = PrivateAttr()
    _a_share_service: AShareService = PrivateAttr()
    _us_stock_service: USStockService = PrivateAttr()
    _hk_stock_service: HKStockService = PrivateAttr()

    def __init__(self):
        """Initialize the market data skill with all required components"""
        super().__init__()
        self._rate_limiter = rate_limiter
        self._a_share_service = AShareService()
        self._us_stock_service = USStockService()
        self._hk_stock_service = HKStockService()
        logger.info("AI-fundin市场数据获取工具已初始化")

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
        从自然语言文本中提取股票代码和名称，支持中文公司名称

        Args:
            text: 用户输入的自然语言文本

        Returns:
            股票代码列表
        """
        symbols = []
        import re

        # 中文公司名称到股票代码的映射
        chinese_company_mapping = {
            # A股 - 银行类
            '平安银行': '000001', '招商银行': '600036', '工商银行': '601398', '建设银行': '601939',
            '农业银行': '601288', '中国银行': '601988', '交通银行': '601328', '中信银行': '601998',
            '光大银行': '601818', '浦发银行': '600000', '民生银行': '600016', '华夏银行': '600015',
            '兴业银行': '601166', '宁波银行': '002142', '南京银行': '601009', '北京银行': '601169',

            # A股 - 白酒类
            '贵州茅台': '600519', '五粮液': '000858', '泸州老窖': '000568', '洋河股份': '002304',
            '山西汾酒': '600809', '古井贡酒': '000596', '今世缘': '603369', '水井坊': '600779',

            # A股 - 保险类
            '中国平安': '601318', '中国人寿': '601628', '中国太保': '601601', '新华保险': '601336',

            # A股 - 科技类
            '海康威视': '002415', '立讯精密': '002475', '京东方': '000725', '中兴通讯': '000063',
            '科大讯飞': '002230', '三六零': '601360', '三安光电': '600703', '歌尔股份': '002241',

            # A股 - 消费类
            '伊利股份': '600887', '海天味业': '603288', '双汇发展': '000895', '青岛啤酒': '600600',
            '海尔智家': '600690', '美的集团': '000333', '格力电器': '000651', '老板电器': '002508',

            # A股 - 医药类
            '恒瑞医药': '600276', '药明康德': '603259', '爱尔眼科': '300015', '片仔癀': '600436',
            '云南白药': '000538', '复星医药': '600196', '长春高新': '000661', '迈瑞医疗': '300760',

            # A股 - 新能源类
            '宁德时代': '300750', '比亚迪': '002594', '隆基绿能': '601012', '通威股份': '600438',
            '阳光电源': '300274', '亿纬锂能': '300014', '赣锋锂业': '002460', '天齐锂业': '002466',

            # A股 - 地产类
            '万科': '000002', '保利发展': '600048', '招商蛇口': '001979', '金地集团': '600383',
            '新城控股': '601155', '绿地控股': '600606', '华夏幸福': '600340', '华侨城': '000069',

            # A股 - 制造业
            '三一重工': '600031', '徐工机械': '000425', '潍柴动力': '000338', '中集集团': '000039',
            '中国中车': '601766', '中国重工': '601989', '中国船舶': '600150', '宝钢股份': '600019',

            # A股 - 交通运输
            '顺丰控股': '002352', '圆通速递': '600233', '中通快递': '02057', '韵达股份': '002120',
            '中国国航': '601111', '南方航空': '600029', '东方航空': '600115', '春秋航空': '601021',

            # A股 - 能源类
            '中国石油': '601857', '中国石化': '600028', '中国海油': '600938', '长江电力': '600900',
            '华能国际': '600011', '国电电力': '600795', '中国神华': '601088', '陕鼓动力': '601369',

            # US Stocks - 科技公司
            '苹果': 'AAPL', '微软': 'MSFT', '谷歌': 'GOOGL', '亚马逊': 'AMZN',
            '特斯拉': 'TSLA', '英伟达': 'NVDA', 'META': 'META', 'META平台': 'META',
            '脸书': 'META', '网飞': 'NFLX', '奈飞': 'NFLX', '推特': 'TWTR',
            '甲骨文': 'ORCL', '奥多比': 'ADBE', '赛富时': 'CRM', '腾讯音乐': 'TME',
            '阿里巴巴': 'BABA', '百度': 'BIDU', '京东': 'JD', '拼多多': 'PDD',
            '蔚来': 'NIO', '理想汽车': 'LI', '小鹏汽车': 'XPEV', '哔哩哔哩': 'BILI',
            '爱奇艺': 'IQ', '网易': 'NTES', '微博': 'WB', '新东方': 'EDU',
            '好未来': 'TAL', '携程': 'TCOM', '贝壳': 'BEKE',

            # US Stocks - 传统行业
            '伯克希尔': 'BRK', '可口可乐': 'KO', '麦当劳': 'MCD', '沃尔玛': 'WMT',
            '迪士尼': 'DIS', '波音': 'BA', '3M': 'MMM', '强生': 'JNJ',
            '辉瑞': 'PFE', '宝洁': 'PG', '耐克': 'NKE', '星巴克': 'SBUX',
            '维萨': 'V', '万事达': 'MA', '美国银行': 'BAC', '摩根大通': 'JPM',
            '高盛': 'GS', '花旗': 'C', '富国银行': 'WFC',

            # HK Stocks - 科技股
            '腾讯': '0700', '腾讯控股': '0700', '阿里巴巴港股': '9988', '美团': '3690',
            '小米': '1810', '小米集团': '1810', '京东集团': '9618', '网易港股': '9999',
            '比亚迪电子': '0285', '联想集团': '0992', '金山软件': '3888', '金蝶国际': '0268',

            # HK Stocks - 金融股
            '港交所': '0388', '香港交易所': '0388', '汇丰': '0005', '汇丰控股': '0005',
            '友邦': '1299', '友邦保险': '1299', '中国太平': '00966', '中银香港': '2388',

            # HK Stocks - 消费股
            '海底捞': '6862', '周黑鸭': '1458', '颐海国际': '1579', '蒙牛乳业': '2319',
            '伊利港股': '6863', '中国飞鹤': '6186', '恒安国际': '1044', '维达国际': '3331',

            # HK Stocks - 地产建筑
            '长和': '0001', '长江实业': '1113', '新世界': '0017', '新鸿基': '0016',
            '恒基地产': '0012', '信和置业': '0083', '恒隆地产': '0101', '九龙仓': '0004',

            # HK Stocks - 能源公用
            '中电': '0002', '香港中华煤气': '0003', '电能实业': '0006', '港灯': '2638',
            '昆仑能源': '0135', '华润电力': '0836', '华能国际': '0902',

            # HK Stocks - 医疗
            '药明生物': '2269', '药明康德': '2359', '中国中药': '00570', '阿里健康': '00241',
            '京东健康': '06618', '平安好医生': '01833',

            # HK Stocks - 通信
            '中国移动': '0941', '中国联通': '0762', '中国电信': '0728', '中国铁塔': '00788',

            # HK Stocks - 其他
            '安踏': '2020', '安踏体育': '2020', '李宁': '2331', '中国旺旺': '0151',
            '康师傅': '0322', '统一': '0220', '万洲国际': '0288', '中芯国际': '0981'
        }

        # 步骤1: 优先处理中文公司名称
        text_clean = text.upper()
        for company_name, symbol in chinese_company_mapping.items():
            # 使用正確的匹配模式，避免部分匹配
            pattern = company_name.upper().replace('(', '\(').replace(')', '\)')
            if re.search(rf'\b{pattern}\b', text_clean):
                symbols.append(symbol)
                # 从文本中移除已匹配的公司名称，避免重复匹配
                text_clean = re.sub(rf'\b{pattern}\b', '', text_clean)

        # 步骤2: 处理股票代码（如果文本中还有）
        # Pattern 1: A股代码 (6位数字)
        matches = re.findall(r'(\d{6})', text_clean)
        symbols.extend([match for match in matches if self._is_valid_share_code(match)])

        # Pattern 2: US stock symbols (AAPL, TSLA, etc.)
        matches = re.findall(r'\b([A-Z]{1,5})\b', text_clean)
        symbols.extend([match for match in matches if self._is_valid_us_symbol(match)])

        # Pattern 3: HK stock symbols (00700, 02318, etc.)
        # 修正：确保只匹配5位数字的港股代码，避免匹配到A股代码的一部分
        matches = re.findall(r'\b0\d{4}\b', text_clean)
        symbols.extend([match for match in matches if self._is_valid_hk_code(match)])

        # 步骤3: 移除重复项并保持顺序
        seen = set()
        unique_symbols = []
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)

        # 步骤4: 港股代码处理 - 去掉前面的0转换为正确的5位格式
        final_symbols = []
        for symbol in unique_symbols:
            if symbol.startswith('0') and len(symbol) == 5:
                final_symbols.append(symbol)
            elif symbol.startswith('0') and len(symbol) == 4:
                # 将4位代码（如0700）转换为5位（0700保持不变）
                final_symbols.append(symbol.zfill(4))
            elif symbol.isdigit() and len(symbol) == 6:
                # A股代码保持不变
                final_symbols.append(symbol)
            else:
                # 美股代码保持大写
                final_symbols.append(symbol.upper())

        return final_symbols[:Config.BATCH_MAX_SYMBOLS]

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