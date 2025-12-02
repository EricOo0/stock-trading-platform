"""
美股服务层
处理美股相关的业务逻辑
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..data_sources.yahoo_finance import YahooFinanceDataSource
from ..data_sources.akshare_data import AkShareDataSource
from ..data_sources.sina_finance import SinaFinanceDataSource
from ..utils.rate_limiter import rate_limiter
from ..utils.validators import validate_stock_symbol, validate_price_data
from ..utils.error_handler import create_error_response, create_success_response, ValidationError
from ..config import Config

logger = logging.getLogger(__name__)

class USStockService:
    """美股服务类"""

    def __init__(self):
        """初始化美股服务"""
        # 美股数据源优先级：Sina Finance -> Yahoo Finance -> AkShare
        # Sina Finance支持美股，格式为gb_ + 股票代码小写
        self.primary_source = SinaFinanceDataSource()
        self.secondary_source = YahooFinanceDataSource()
        self.fallback_source = AkShareDataSource()
        self.market_type = "US"
        self.logger = logging.getLogger(self.__class__.__name__)
        # 导入并使用全局rate_limiter
        from ..utils.rate_limiter import rate_limiter
        self.rate_limiter = rate_limiter

    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取美股单只股票行情

        Args:
            symbol: 美股股票代码

        Returns:
            股票行情数据或错误响应
        """
        start_time = datetime.now()

        try:
            # 1. 输入验证
            validation_result = validate_stock_symbol(symbol, self.market_type)
            if not validation_result:
                return create_error_response(
                    symbol=symbol,
                    error_code="INVALID_SYMBOL",
                    error_message=f"无效的股票代码: {symbol}, {validation_result.get_errors()[0]}",
                    suggestion="请提供有效的美股代码：1-5位字母，如AAPL、TSLA、GOOGL"
                )

            # 2. 限流检查 - 美股限流较严格（60次/小时）
            if not rate_limiter.check_and_consume(self.market_type):
                rate_info = rate_limiter.get_rate_limit_info(self.market_type)
                return create_error_response(
                    symbol=symbol,
                    error_code="RATE_LIMITED",
                    error_message=f"美股市场请求频率超限（剩余配额：{rate_info['remaining_tokens']}）",
                    suggestion="请等待配额重置后再试，美股市场限制为60次/小时"
                )

            # 3. 获取股价数据 - 美股数据源优先级：Sina Finance -> Yahoo Finance -> AkShare
            data_sources = [
                ("Sina Finance", self.primary_source),
                ("Yahoo Finance", self.secondary_source),
                ("AkShare", self.fallback_source)
            ]
            
            for source_name, data_source in data_sources:
                try:
                    self.logger.info(f"使用{source_name}获取美股 {symbol} 数据")
                    data = data_source.get_stock_quote(symbol, self.market_type)
                    response = self._process_data(data, start_time, source_name.lower().replace(" ", "_"))
                    self.logger.info(f"成功从{source_name}获取 {symbol} 数据")
                    return response
                except Exception as data_error:
                    self.logger.warning(f"{source_name}获取美股 {symbol} 数据失败: {data_error}，尝试下一个数据源")
                    continue
            
            # 所有数据源都失败
            self.logger.error(f"所有数据源获取美股 {symbol} 数据失败")
            return create_error_response(
                symbol=symbol,
                error_code="ALL_SOURCES_FAILED",
                error_message="所有数据源均无法获取数据",
                suggestion="请稍后重试，或检查股票代码是否正确"
            )

        except Exception as e:
            self.logger.error(f"获取美股 {symbol} 数据时发生未预期错误: {e}")
            return create_error_response(
                symbol=symbol,
                error_code="INTERNAL_ERROR",
                error_message="系统处理错误",
                suggestion="请联系技术支持"
            )

    def _process_data(self, raw_data: Dict[str, Any], start_time: datetime, data_source: str) -> Dict[str, Any]:
        """
        处理美股数据

        Args:
            raw_data: 原始股票数据
            start_time: 请求开始时间
            data_source: 数据源

        Returns:
            处理后的响应数据
        """
        try:
            # 数据验证
            price_validation = validate_price_data(raw_data)
            if not price_validation:
                raise ValidationError("price_data", raw_data, price_validation.get_errors()[0])

            # 计算响应时间
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000

            # 构建标准响应格式
            return create_success_response(
                symbol=raw_data["symbol"],
                data=raw_data,
                data_source=data_source,
                cache_hit=False,
                response_time_ms=response_time_ms
            )

        except ValidationError as e:
            return create_error_response(
                symbol=raw_data.get("symbol", "unknown"),
                error_code="VALIDATION_ERROR",
                error_message=f"数据验证失败: {str(e)}",
                suggestion="数据源返回异常数据，请稍后重试"
            )
        except Exception as e:
            logger.error(f"美股数据处理和验证失败: {e}")
            return create_error_response(
                symbol=raw_data.get("symbol", "unknown"),
                error_code="PROCESSING_ERROR",
                error_message="数据处理和验证失败",
                suggestion="请稍后重试"
            )

    def get_market_overview(self) -> Dict[str, Any]:
        """获取美股市场概况"""
        try:
            # 美股主要指数和大盘股
            indices = {
                "^GSPC": "标普500",
                "^DJI": "道琼斯工业平均",
                "^IXIC": "纳斯达克综合",
                "AAPL": "苹果",
                "MSFT": "微软",
                "GOOGL": "谷歌",
                "AMZN": "亚马逊",
                "TSLA": "特斯拉"
            }

            results = []
            for symbol in indices:
                try:
                    result = self.get_stock_quote(symbol)
                    if result.get("status") == "success":
                        data = result["data"]
                        results.append({
                            "symbol": symbol,
                            "name": indices[symbol],
                            "current_value": data["current_price"],
                            "change_percent": data.get("change_percent", 0.0)
                        })
                except Exception as e:
                    self.logger.warning(f"获取美股概览项目 {symbol} 失败: {e}")
                    continue

            return {
                "status": "success" if results else "partial",
                "market": self.market_type,
                "indices": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
                "currency": "USD"
            }

        except Exception as e:
            self.logger.error(f"获取美股市场概况失败: {e}")
            return create_error_response(
                symbol="US-market",
                error_code="MARKET_OVERVIEW_ERROR",
                error_message="美股市场概况获取失败",
                suggestion="请稍后重试"
            )

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取美股行情数据

        Args:
            symbols: 美股股票代码列表

        Returns:
            批量查询结果
        """
        start_time = datetime.now()

        try:
            # 验证股票代码列表
            valid_symbols = []
            for symbol in symbols:
                validation = validate_stock_symbol(symbol, self.market_type)
                if validation:
                    valid_symbols.append(symbol)
                else:
                    self.logger.warning(f"跳过无效美股代码: {symbol}")

            if not valid_symbols:
                return create_error_response(
                    symbol=",".join(symbols),
                    error_code="INVALID_SYMBOL",
                    error_message="所有股票代码均无效",
                    suggestion="请检查美股代码格式：1-5位字母"
                )

            # 限制批量查询数量
            if len(valid_symbols) > Config.BATCH_MAX_SYMBOLS:
                valid_symbols = valid_symbols[:Config.BATCH_MAX_SYMBOLS]
                self.logger.warning(f"美股批量查询数量超过限制，只处理前{len(valid_symbols)}只股票")

            results = []
            for symbol in valid_symbols:
                try:
                    # 批量查询使用较低的限流额度
                    if not rate_limiter.check_and_consume(self.market_type, 0.5):
                        self.logger.warning(f"美股批量查询 {symbol} 被限流跳过")
                        results.append(create_error_response(
                            symbol=symbol,
                            error_code="RATE_LIMITED",
                            error_message="美股批量查询超出限流，跳过该股票",
                            suggestion="减少批量查询数量或稍后重试"
                        ))
                        continue

                    result = self.get_stock_quote(symbol)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"美股批量查询 {symbol} 失败: {e}")
                    results.append(create_error_response(
                        symbol=symbol,
                        error_code="BATCH_ERROR",
                        error_message="单只股票查询失败",
                        suggestion="单独查询该股票"
                    ))

            # 汇总结果
            end_time = datetime.now()
            total_response_time_ms = (end_time - start_time).total_seconds() * 1000

            successful_count = sum(1 for r in results if r.get("status") == "success")
            failed_count = len(results) - successful_count

            return {
                "status": "partial" if failed_count > 0 else "success",
                "count": len(results),
                "successful_count": successful_count,
                "failed_count": failed_count,
                "success_rate": successful_count / len(results) if results else 0.0,
                "symbols": valid_symbols,
                "results": results,
                "timestamp": end_time.isoformat(),
                "currency": "USD",
                "market": self.market_type,
                "total_response_time_ms": total_response_time_ms
            }

        except Exception as e:
            self.logger.error(f"美股批量查询失败: {e}")
            return create_error_response(
                symbol=",".join(symbols[:3]) + "..." if len(symbols) > 3 else ",".join(symbols),
                error_code="BATCH_ERROR",
                error_message="美股批量查询处理失败",
                suggestion="请减少股票数量或稍后重试"
            )

    def get_historical_data(self, symbol: str, period: str = "30d", interval: str = "1d") -> Dict[str, Any]:
        """
        获取美股历史数据

        Args:
            symbol: 美股股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 时间间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            历史数据或错误响应
        """
        start_time = datetime.now()

        try:
            # 1. 输入验证
            validation_result = validate_stock_symbol(symbol, self.market_type)
            if not validation_result:
                return create_error_response(
                    symbol=symbol,
                    error_code="INVALID_SYMBOL",
                    error_message=f"无效的股票代码: {symbol}",
                    suggestion="请提供有效的美股代码：1-5位字母"
                )

            # 2. 速率限制检查
            if not self.rate_limiter.check_and_consume(self.market_type):
                return create_error_response(
                    symbol=symbol,
                    error_code="RATE_LIMIT_EXCEEDED",
                    error_message="请求过于频繁，请稍后再试",
                    suggestion="请降低查询频率，或稍后再试"
                )

            # 3. 获取历史数据 - 尝试所有可用数据源
            data_sources = [
                ("Sina Finance", self.primary_source),
                ("Yahoo Finance", self.secondary_source),
                ("AkShare", self.fallback_source)
            ]
            
            for source_name, data_source in data_sources:
                try:
                    self.logger.info(f"尝试从 {source_name} 获取美股 {symbol} 历史数据")
                    historical_data = data_source.get_historical_data(symbol, self.market_type, period, interval)
                    
                    if historical_data:
                        self.logger.info(f"成功从 {source_name} 获取 {symbol} 历史数据 ({len(historical_data)}条)")
                        
                        # 4. 返回成功响应
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        return create_success_response(
                            symbol=symbol,
                            data=historical_data,
                            data_source=source_name.lower().replace(" ", "_"),
                            cache_hit=False,
                            response_time_ms=response_time
                        )
                    else:
                        self.logger.warning(f"{source_name} 返回空数据")
                        
                except Exception as e:
                    self.logger.warning(f"{source_name} 获取历史数据失败: {str(e)}")
                    continue

            # 所有数据源都失败
            return create_error_response(
                symbol=symbol,
                error_code="NO_DATA_AVAILABLE",
                error_message="所有数据源均无法获取该股票的历史数据",
                suggestion="请检查股票代码是否正确，或稍后再试"
            )

        except Exception as e:
            self.logger.error(f"获取历史数据失败: {str(e)}")
            return create_error_response(
                symbol=symbol,
                error_code="INTERNAL_ERROR",
                error_message=f"获取历史数据时发生错误: {str(e)}",
                suggestion="请稍后重试，或联系技术支持"
            )

    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        try:
            # 获取限流器统计
            rate_stats = rate_limiter.get_global_stats()

            # 获取数据源状态
            primary_status = self.primary_source.get_data_source_info()

            return {
                "market": self.market_type,
                "rate_limit_stats": rate_stats,
                "primary_source": primary_status,
                "summary": f"{self.market_type}服务运行正常" if self._is_healthy() else f"{self.market_type}服务有异常",
                "timestamp": datetime.now().isoformat(),
                "currency": "USD"
            }

        except Exception as e:
            self.logger.error(f"获取美股服务统计信息失败: {e}")
            return {
                "market": self.market_type,
                "error": f"统计信息获取失败: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _is_healthy(self) -> bool:
        """检查服务健康状况"""
        try:
            # 简单健康检查：尝试连接主数据源
            return self.primary_source.test_connection()
        except Exception:
            return False