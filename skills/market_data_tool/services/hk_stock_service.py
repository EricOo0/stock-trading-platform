"""
港股服务层
处理港股相关的业务逻辑
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..data_sources.yahoo_finance import YahooFinanceDataSource
from ..utils.rate_limiter import rate_limiter
from ..utils.validators import validate_stock_symbol, validate_price_data
from ..utils.error_handler import create_error_response, create_success_response, ValidationError
from ..config import Config

logger = logging.getLogger(__name__)

class HKStockService:
    """港股服务类"""

    def __init__(self):
        """初始化港股服务"""
        self.primary_source = YahooFinanceDataSource()
        self.market_type = "HK"
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股单只股票行情

        Args:
            symbol: 港股股票代码

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
                    suggestion="请提供有效的港股代码：5位数字且以0开头，如00700、02318、09988"
                )

            # 2. 限流检查 - 港股限流较严格（60次/小时）
            if not rate_limiter.check_and_consume(self.market_type):
                rate_info = rate_limiter.get_rate_limit_info(self.market_type)
                return create_error_response(
                    symbol=symbol,
                    error_code="RATE_LIMITED",
                    error_message=f"港股市场请求频率超限（剩余配额：{rate_info['remaining_tokens']}）",
                    suggestion="请等待配额重置后再试，港股市场限制为60次/小时"
                )

            # 3. 获取股价数据 - 港股主要由Yahoo Finance提供
            try:
                self.logger.info(f"使用Yahoo Finance获取港股 {symbol} 数据")
                data = self.primary_source.get_stock_quote(symbol, self.market_type)
                response = self._process_data(data, start_time, "yahoo")
                self.logger.info(f"成功从Yahoo Finance获取 {symbol} 数据")
                return response

            except Exception as data_error:
                self.logger.error(f"获取港股 {symbol} 数据失败: {data_error}")
                return create_error_response(
                    symbol=symbol,
                    error_code="API_ERROR",
                    error_message=f"数据源返回错误：{str(data_error)}",
                    suggestion="请稍后重试，或检查股票代码是否正确"
                )

        except Exception as e:
            self.logger.error(f"获取港股 {symbol} 数据时发生未预期错误: {e}")
            return create_error_response(
                symbol=symbol,
                error_code="INTERNAL_ERROR",
                error_message="系统处理错误",
                suggestion="请联系技术支持"
            )

    def _process_data(self, raw_data: Dict[str, Any], start_time: datetime, data_source: str) -> Dict[str, Any]:
        """
        处理港股数据

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
            logger.error(f"港股数据处理和验证失败: {e}")
            return create_error_response(
                symbol=raw_data.get("symbol", "unknown"),
                error_code="PROCESSING_ERROR",
                error_message="数据处理和验证失败",
                suggestion="请稍后重试"
            )

    def get_market_overview(self) -> Dict[str, Any]:
        """获取港股市场概况"""
        try:
            # 港股主要指数和恒指成分股
            indices = {
                "^HSI": "恒生指数",
                "^HSCEI": "恒生中国企业指数",
                "^HSTECH": "恒生科技指数",
                "00700": "腾讯控股",
                "02318": "中国平安",
                "09988": "阿里巴巴-SW",
                "03690": "美团-W",
                "01810": "小米集团-W",
                "00388": "香港交易所"
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
                    self.logger.warning(f"获取港股概览项目 {symbol} 失败: {e}")
                    continue

            return {
                "status": "success" if results else "partial",
                "market": self.market_type,
                "indices": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
                "currency": "HKD"
            }

        except Exception as e:
            self.logger.error(f"获取港股市场概况失败: {e}")
            return create_error_response(
                symbol="HK-market",
                error_code="MARKET_OVERVIEW_ERROR",
                error_message="港股市场概况获取失败",
                suggestion="请稍后重试"
            )

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取港股行情数据

        Args:
            symbols: 港股股票代码列表

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
                    self.logger.warning(f"跳过无效港股代码: {symbol}")

            if not valid_symbols:
                return create_error_response(
                    symbol=",".join(symbols),
                    error_code="INVALID_SYMBOL",
                    error_message="所有股票代码均无效",
                    suggestion="请检查港股代码格式：5位数字且以0开头"
                )

            # 限制批量查询数量
            if len(valid_symbols) > Config.BATCH_MAX_SYMBOLS:
                valid_symbols = valid_symbols[:Config.BATCH_MAX_SYMBOLS]
                self.logger.warning(f"港股批量查询数量超过限制，只处理前{len(valid_symbols)}只股票")

            results = []
            for symbol in valid_symbols:
                try:
                    # 批量查询使用较低的限流额度
                    if not rate_limiter.check_and_consume(self.market_type, 0.5):
                        self.logger.warning(f"港股批量查询 {symbol} 被限流跳过")
                        results.append(create_error_response(
                            symbol=symbol,
                            error_code="RATE_LIMITED",
                            error_message="港股批量查询超出限流，跳过该股票",
                            suggestion="减少批量查询数量或稍后重试"
                        ))
                        continue

                    result = self.get_stock_quote(symbol)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"港股批量查询 {symbol} 失败: {e}")
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
                "currency": "HKD",
                "market": self.market_type,
                "total_response_time_ms": total_response_time_ms
            }

        except Exception as e:
            self.logger.error(f"港股批量查询失败: {e}")
            return create_error_response(
                symbol=",".join(symbols[:3]) + "..." if len(symbols) > 3 else ",".join(symbols),
                error_code="BATCH_ERROR",
                error_message="港股批量查询处理失败",
                suggestion="请减少股票数量或稍后重试"
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
                "currency": "HKD"
            }

        except Exception as e:
            self.logger.error(f"获取港股服务统计信息失败: {e}")
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