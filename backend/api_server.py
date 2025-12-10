#!/usr/bin/env python3
"""
后端API代理服务 - 连接前端和market_data_tool skill
"""

import sys
import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import datetime as dt
import math
from typing import Dict, List

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 添加agent目录到Python路径 (for utils.logging)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent'))

# 导入 Tool Registry
from tools.registry import Tools

# 初始化全局 Tools 实例
# 初始化全局 Tools 实例
tools = Tools()

# Initialize Simulation Service
from services.simulation_service import SimulationService
simulation_service = SimulationService()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import mimetypes

class MarketDataAPIHandler(BaseHTTPRequestHandler):
    """市场数据API处理器"""
    
    def _clean_nans(self, obj):
        """Recursively replace NaNs with None for JSON serialization"""
        if isinstance(obj, float):
            return None if math.isnan(obj) or math.isinf(obj) else obj
        if isinstance(obj, dict):
            return {k: self._clean_nans(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._clean_nans(i) for i in obj]
        return obj

    def _set_headers(self, status=200, content_type='application/json'):
        """设置响应头"""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self._set_headers(200)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # Static file serving for reports
        if path.startswith('/static/reports/'):
            try:
                # Security check: prevent directory traversal
                file_name = os.path.basename(path)
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'reports', file_name)
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    # Guess MIME type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if mime_type is None:
                        mime_type = 'application/octet-stream'
                        
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        
                    self.send_response(200)
                    self.send_header('Content-Type', mime_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'error': 'File not found'}).encode())
                    return
            except Exception as e:
                logger.error(f"Error serving static file: {e}")
                self._set_headers(500)
                return

        if path == '/api/market-data/hot':
            self.handle_hot_stocks()
        elif path.startswith('/api/market/historical/'):
            self.handle_historical_data(path, query_params)
        elif path.startswith('/api/macro-data/historical/'):
            self.handle_macro_historical_data(path, query_params)
        elif path == '/api/macro-data/fed-implied-probability':
            self.handle_fed_implied_probability()
        elif path.startswith('/api/market/technical/'):
            self.handle_technical_analysis(path, query_params)
        elif path == '/api/web-search':
            self.handle_web_search(query_params)
        elif path.startswith('/api/financial-report/'):
            self.handle_financial_report(path)
        elif path.startswith('/api/simulation/'):
            self.handle_simulation(path, query_params)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/market-data':
            self.handle_market_data()
        elif path == '/api/tools/financial_report_tool/get_financial_indicators':
            self.handle_financial_indicators()
        elif path.startswith('/api/simulation/'):
            self.handle_simulation_post(path)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def handle_market_data(self):
        """处理市场数据查询"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            query = request_data.get('query', '')
            logger.info(f"收到查询请求: {query}")
            
            # 使用 Tools 解析和获取数据
            symbols = tools.extract_symbols(query)
            
            if not symbols:
                 # 没找到代码，返回错误
                response = {
                    'status': 'error',
                    'symbol': query,
                    'message': '未能识别股票代码',
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'real',
                    'cache_hit': False,
                    'response_time_ms': 0
                }
            else:
                results = []
                for symbol in symbols:
                    res = tools.get_stock_price(symbol)
                    if res and "error" not in res:
                        results.append({
                            "status": "success",
                            "symbol": symbol,
                            "data": res,
                            "timestamp": datetime.now().isoformat(),
                            "cache_hit": False,
                            "response_time_ms": 0
                        })
                    else:
                        results.append({
                            "status": "error",
                            "symbol": symbol,
                            "error_message": res.get("error", "查询失败") if res else "查询失败"
                        })
                
                # 构造响应
                if len(results) == 1:
                    # 单个结果
                    first = results[0]
                    if first["status"] == "success":
                        response = {
                            'status': 'success',
                            'symbol': first['symbol'],
                            'data': first['data'],
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'real',
                            'cache_hit': False,
                            'response_time_ms': 0
                        }
                    else:
                        response = {
                            'status': 'error',
                            'symbol': first['symbol'],
                            'message': first.get('error_message'),
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'real'
                        }
                else:
                    # 多个结果
                    success_count = sum(1 for r in results if r["status"] == "success")
                    response = {
                        'status': 'success' if success_count == len(results) else 'partial',
                        'results': results,
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'real'
                    }

            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"处理查询请求失败: {str(e)}")
            error_response = {
                'status': 'error',
                'symbol': '',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'real',
                'cache_hit': False,
                'response_time_ms': 0
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
    
    def handle_hot_stocks(self):
        """处理热门股票查询"""
        try:
            # 定义热门股票列表
            hot_stocks = ['000001', '600036', 'AAPL', 'TSLA', '00700', '000002']
            results = []
            
            for symbol in hot_stocks:
                try:
                    result = tools.get_stock_price(symbol)
                    if result and "error" not in result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"获取{symbol}数据失败: {str(e)}")
                    continue
            
            response = {
                'status': 'success',
                'data': results,
                'timestamp': datetime.now().isoformat(),
                'count': len(results)
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode())
            
        except Exception as e:
            logger.error(f"处理热门股票请求失败: {str(e)}")
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
    
    def handle_historical_data(self, path: str, query_params: Dict[str, List[str]]):
        """处理历史数据查询"""
        try:
            # 从路径中提取股票代码
            path_parts = path.split('/')
            if len(path_parts) < 4:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid path format'}).encode())
                return
            
            symbol = path_parts[-1]  # 获取路径最后一部分作为股票代码
            
            # 获取查询参数并转换格式
            period = query_params.get('period', ['30d'])[0] if 'period' in query_params else '30d'
            count = int(query_params.get('count', ['30'])[0]) if 'count' in query_params else 30
            
            # 转换周期格式（前端使用DAY，Yahoo使用1d）
            if period.upper() == 'DAY':
                period = '1d'
            elif period.upper() == 'WEEK':
                period = '1wk'
            elif period.upper() == 'MONTH':
                period = '1mo'
            
            logger.info(f"收到历史数据查询请求: {symbol}, 周期: {period}, 数量: {count}")
            
            # 调用skill获取历史数据
            # 导入skill实例
            # from skills.market_data_tool.skill import MarketDataSkill
            # skill = MarketDataSkill()
            
            # 获取历史数据
            result_data = tools.get_historical_data(symbol, period, '1d')
            
            # 处理结果
            if result_data:
                # 限制返回的数据条数
                historical_data = result_data[:count]
                
                response = {
                    'status': 'success',
                    'symbol': symbol,
                    'data': historical_data,
                    'count': len(historical_data),
                    'period': period,
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'real'
                }
                
                self._set_headers(200)
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            else:
                # 返回错误信息
                error_response = {
                    'status': 'error',
                    'symbol': symbol,
                    'message': '获取历史数据失败',
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'real'
                }
                self._set_headers(200)  # 仍然返回200，但包含错误信息
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
                
        except Exception as e:
            logger.error(f"处理历史数据查询请求失败: {str(e)}")
            error_response = {
                'status': 'error',
                'symbol': '',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'real'
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())

    def handle_technical_analysis(self, path: str, query_params: Dict[str, List[str]]):
        """处理技术面分析请求"""
        try:
            # 从路径中提取股票代码
            path_parts = path.split('/')
            if len(path_parts) < 4:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid path format'}).encode())
                return
            
            symbol = path_parts[-1]
            period = query_params.get('period', ['1y'])[0]
            
            logger.info(f"收到技术分析请求: {symbol}, 周期: {period}")
            
            # 获取历史数据
            # from skills.market_data_tool.skill import MarketDataSkill
            # skill = MarketDataSkill()
            # 强制使用日线数据进行指标计算
            data = tools.get_historical_data(symbol, period, '1d')
            
            if not data:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'No data found'}).encode())
                return

            # 转换为DataFrame并计算指标
            import pandas as pd
            df = pd.DataFrame(data)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                df = df.sort_values('timestamp')
            
            # 确保数值列为float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = df[col].astype(float)

            # 1. 计算移动平均线 (MA)
            for window in [5, 10, 20, 30, 60]:
                df[f'ma{window}'] = df['close'].rolling(window=window).mean()

            # 2. 计算布林带 (BOLL)
            # 中轨 = 20日均线
            # 上轨 = 中轨 + 2 * 标准差
            # 下轨 = 中轨 - 2 * 标准差
            df['boll_mid'] = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            df['boll_upper'] = df['boll_mid'] + 2 * std20
            df['boll_lower'] = df['boll_mid'] - 2 * std20

            # 3. 计算 MACD
            # EMA12, EMA26
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd_dif'] = exp12 - exp26
            df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
            df['macd_bar'] = 2 * (df['macd_dif'] - df['macd_dea'])

            # 4. 计算 RSI (14日)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi14'] = 100 - (100 / (1 + rs))
            # 填充NaN (早期数据可能没有RSI)
            df['rsi14'] = df['rsi14'].fillna(50) 

            # 5. 计算 KDJ (9, 3, 3)
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            # Pandas没有直接的SMA/EMA递归计算，这里用ewm模拟或者循环
            # K = 2/3 * PrevK + 1/3 * RSV
            # D = 2/3 * PrevD + 1/3 * K
            # J = 3 * K - 2 * D
            # 为简单起见，使用ewm(com=2)近似 1/3权重
            df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
            df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
            df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

            # 处理NaN: 将NaN转换为None，以便前端JSON序列化为null
            # Recharts等图表库通常能更好地处理null(断点)而不是0
            df = df.replace({float('nan'): None, float('inf'): None, float('-inf'): None})
            
            # 转换回字典列表
            # datetime需要转回字符串
            if 'timestamp' in df.columns:
                # 检查是否为datetime类型
                if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d')
                else:
                    # 如果是字符串或其他类型，尝试转换或保持原样
                    # 假设如果是字符串已经是 ISO 格式，或者我们需要统一格式
                    try:
                        # 尝试转换为 datetime 然后再格式化，以确保格式统一
                        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
                    except Exception:
                        # 如果转换失败，保留原样
                        pass
            
            technical_data = df.to_dict('records')

            response = {
                'status': 'success',
                'symbol': symbol,
                'data': technical_data,
                'count': len(technical_data),
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode())

        except Exception as e:
            logger.error(f"处理技术分析请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
    
    def handle_web_search(self, query_params: Dict[str, List[str]]):
        """处理网络搜索请求"""
        try:
            query = query_params.get('q', [''])[0]
            
            if not query:
                error_response = {
                    'status': 'error',
                    'message': '搜索查询不能为空',
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(400)
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
                return
            
            logger.info(f"执行网络搜索: {query}")
            
            # 初始化WebSearchSkill
            # 配置为新闻搜索模式，限制最近7天，确保获取相关性强且即时的新闻
            # web_search_skill = WebSearchSkill(...)
            
            # 执行搜索
            results = tools.search_market_news(query, provider='auto') # Implicitly topic=news
            
            if results:
                response = {
                    'status': 'success',
                    'query': query,
                    'results': results,  # Return structured array
                    'provider': 'auto',
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(200)
            else:
                response = {
                    'status': 'error',
                    'message': '搜索失败或无结果',
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(500)
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            logger.error(f"处理网络搜索请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())

    def handle_financial_report(self, path: str):
        """处理财报分析请求 /api/financial-report/{symbol}"""
        try:
            path_parts = path.split('/')
            
            # Check for analyze request: /api/financial-report/analyze/{symbol}
            if len(path_parts) >= 5 and path_parts[3] == 'analyze':
                symbol = path_parts[4]
                logger.info(f"分析财报数据: {symbol}")
                
                # from skills.financial_report_tool.skill import FinancialReportSkill
                # skill = FinancialReportSkill()
                result = tools.analyze_report(symbol)
                
                self._set_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False, default=str).encode())
                return

            # Extract symbol from path
            # Path format: /api/financial-report/AAPL
            symbol = path_parts[-1]
            
            if not symbol:
                self._set_headers(400)
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Symbol is required'}).encode())
                return

            logger.info(f"获取财报数据: {symbol}")
            
            # Import here to avoid circular dependency if any, or just convenience
            # from skills.financial_report_tool.skill import FinancialReportSkill
            
            # skill = FinancialReportSkill()
            
            # 1. Get Metrics
            metrics_result = tools.get_financial_metrics(symbol)
            
            # 2. Get Latest Report Metadata
            report_result = tools.get_company_report(symbol)
            
            # Extract metrics array from metrics_result
            metrics_array = []
            if metrics_result.get("status") == "success":
                metrics_array = metrics_result.get("metrics", [])
            
            response = {
                'status': 'success',
                'symbol': symbol,
                'metrics': metrics_array,  # Array format for frontend
                'latest_report': report_result if report_result.get('status') in ['success', 'partial'] else None,
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode())

        except Exception as e:
            logger.error(f"处理财报请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self._set_headers(500)
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

    def handle_financial_indicators(self):
        """处理财务指标请求 POST /api/tools/financial_report_tool/get_financial_indicators"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            symbol = request_data.get('symbol', '')
            years = request_data.get('years', 3)
            use_cache = request_data.get('use_cache', True)
            
            if not symbol:
                self._set_headers(400)
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Symbol is required'}).encode())
                return

            logger.info(f"获取财务指标: {symbol}, years={years}")
            
            # Call unified registry method which handles fallback
            indicators_data = tools.get_financial_indicators(symbol, years=years)
            
            # Detect market for response
            market = tools._detect_market(symbol)
            
            # Wrap in proper response format for frontend
            response = {
                'status': 'success',
                'symbol': symbol,
                'market': market,
                'data_source': 'registry',  # Could be enhanced to track actual source
                'indicators': indicators_data,  # Wrap the indicators
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False, default=str).encode())

        except Exception as e:
            logger.error(f"处理财务指标请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self._set_headers(500)
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

    def handle_macro_historical_data(self, path: str, query_params: Dict[str, List[str]]):
        """处理宏观数据历史查询"""
        try:
            # 从路径中提取指标名称
            path_parts = path.split('/')
            if len(path_parts) < 4:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid path format'}).encode())
                return
            
            indicator = path_parts[-1]
            
            # 获取查询参数
            period = query_params.get('period', ['1y'])[0] if 'period' in query_params else '1y'
            
            logger.info(f"收到宏观历史数据查询请求: {indicator}, 周期: {period}")
            
            logger.info(f"收到宏观历史数据查询请求: {indicator}, 周期: {period}")
            
            # skill = MacroDataSkill()
            # result = skill.get_historical_data(indicator, period)
            result = tools.get_macro_history(indicator, period)

            # Clean NaNs before sending
            result = self._clean_nans(result)
            
            if 'error' not in result:
                response = {
                    'status': 'success',
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            else:
                error_response = {
                    'status': 'error',
                    'message': result.get('error', '获取数据失败'),
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
                
        except Exception as e:
            logger.error(f"处理宏观历史数据查询请求失败: {str(e)}")
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())
    
    def handle_fed_implied_probability(self):
        """处理美联储降息概率查询 (基于 Implied Rate)"""
        try:
            logger.info("Handling Fed Implied Probability request")
            
            # 1. Fetch Current Fed Target Upper Limit (DFEDTARU) from FRED
            # Use get_macro_history directly via tools which routes to FredTool
            # We fetch 1y to be safe and get the latest
            fed_data = tools.get_macro_history("DFEDTARU", "1y")
            
            current_target_upper = 5.50 # Default fallback
            current_date = ""
            
            if fed_data and "data" in fed_data and len(fed_data["data"]) > 0:
                # Get latest value
                latest = fed_data["data"][-1]
                if latest.get("value") is not None:
                    current_target_upper = float(latest["value"])
                    current_date = latest.get("date")
            
            # Current Target Bin is [Upper-0.25, Upper]
            # e.g. 4.0 -> Bin 3.75-4.00. Midpoint 3.875
            current_target_mid = current_target_upper - 0.125
            
            # 2. Fetch ZQ=F (30-Day Fed Funds Futures) from yfinance
            import yfinance as yf
            ticker = yf.Ticker("ZQ=F")
            # Fetch brief history to get latest 'Close'
            hist = ticker.history(period="5d")
            
            if hist.empty:
                raise Exception("Failed to fetch ZQ=F futures data")
                
            zq_price = hist["Close"].iloc[-1]
            implied_rate = 100 - zq_price # e.g. 100 - 96.345 = 3.655
            
            # 3. Calculate Bin Distribution
            # We assume the implied rate is the weighted average of two adjacent bins
            # Bin width is 0.25
            
            # Function to get bin name: 3.75-4.00 -> "375-400"
            def get_bin_name(midpoint):
                low = int((midpoint - 0.125) * 100)
                high = int((midpoint + 0.125) * 100)
                return f"{low}-{high}"
            
            # Find the two bins bracketing the implied rate
            # Standard bins are centered at ..., 3.625, 3.875, 4.125, ...
            # Normalized implied rate to finding nearest midpoints
            # x = (rate - 0.125) / 0.25
            
            # Let's project relative to current target
            # e.g. Current Mid: 3.875. Implied: 3.655.
            # Difference from current: -0.22
            
            # Base bin midpoint (nearest 0.25 step)
            # 3.655 -> nearest standard midpoints are 3.625 (Bin 3.50-3.75) and 3.875 (Bin 3.75-4.00)
            
            # To be precise:
            # Shift implied rate to align with bin centers
            # Center of Bin N = 0.125 + N * 0.25
            
            # Simple Linear Interpolation between two nearest bins
            # Lower Bin Center
            bin_step = 0.25
            # Shift by offset to align 0.125 to 0
            shifted_rate = implied_rate - 0.125
            lower_bin_index = math.floor(shifted_rate / bin_step)
            
            lower_bin_mid = 0.125 + lower_bin_index * bin_step
            upper_bin_mid = lower_bin_mid + bin_step
            
            # Weight of Upper Bin
            # If Implied = 3.655. Lower Mid (3.625). Upper Mid (3.875).
            # Weight Upper = (3.655 - 3.625) / 0.25 = 0.03 / 0.25 = 0.12 (12%)
            # Weight Lower = 1 - 0.12 = 0.88 (88%)
            
            weight_upper = (implied_rate - lower_bin_mid) / bin_step
            weight_lower = 1.0 - weight_upper
            
            # Clamp weights (in case implied rate is erratic, though unlikely for spread)
            weight_upper = max(0.0, min(1.0, weight_upper))
            weight_lower = 1.0 - weight_upper
            
            bins = [
                {
                    "bin": get_bin_name(lower_bin_mid),
                    "prob": round(weight_lower * 100, 1),
                    "is_current": abs(lower_bin_mid - current_target_mid) < 0.01
                },
                {
                    "bin": get_bin_name(upper_bin_mid),
                    "prob": round(weight_upper * 100, 1),
                    "is_current": abs(upper_bin_mid - current_target_mid) < 0.01
                }
            ]
            
            # Identify which is "Current"
            # We already marked it. Now add 'label' e.g. "Current"
            
            results = {
                "status": "success",
                "current_target_rate": f"{current_target_upper-0.25:.2f}-{current_target_upper:.2f}",
                "implied_rate": round(implied_rate, 3),
                "data": bins,
                "timestamp": datetime.now().isoformat()
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode())

        except Exception as e:
            logger.error(f"处理美联储概率请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())

    def handle_simulation(self, path: str, query_params: Dict[str, List[str]]):
        """处理模拟交易GET请求"""
        try:
            if path == '/api/simulation/tasks':
                tasks = simulation_service.get_all_tasks()
                self._set_headers(200)
                self.wfile.write(json.dumps({'status': 'success', 'data': tasks}, ensure_ascii=False, default=str).encode())
            elif path.startswith('/api/simulation/task/'):
                # Get single task
                task_id = path.split('/')[-1]
                task = simulation_service.get_task(task_id)
                if task:
                    self._set_headers(200)
                    self.wfile.write(json.dumps({'status': 'success', 'data': task}, ensure_ascii=False, default=str).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'status': 'error', 'message': 'Task not found'}).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
        except Exception as e:
            logger.error(f"Simulation GET error: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

    def handle_simulation_post(self, path: str):
        """处理模拟交易POST请求"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            if path == '/api/simulation/create':
                symbol = request_data.get('symbol')
                if not symbol:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'status': 'error', 'message': 'Symbol required'}).encode())
                    return
                task = simulation_service.create_task(symbol)
                self._set_headers(200)
                self.wfile.write(json.dumps({'status': 'success', 'data': task}, ensure_ascii=False, default=str).encode())
            
            elif path == '/api/simulation/run':
                task_id = request_data.get('task_id')
                if not task_id:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'status': 'error', 'message': 'Task ID required'}).encode())
                    return
                
                # Run simulation step
                result = simulation_service.run_daily_simulation(task_id, tools)
                self._set_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False, default=str).encode())
            
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())

        except Exception as e:
            logger.error(f"Simulation POST error: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())


def run_server(port=8000):
    """运行API服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MarketDataAPIHandler)
    logger.info(f"市场数据API服务器启动，端口: {port}")
    logger.info(f"API端点:")
    logger.info(f"  POST /api/market-data - 查询股票数据")
    logger.info(f"  GET  /api/market-data/hot - 获取热门股票")
    logger.info(f"  GET  /api/market/historical/<symbol> - 获取历史数据")
    logger.info(f"  GET  /api/market/technical/<symbol> - 获取技术分析数据(含指标)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
        httpd.shutdown()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='市场数据API服务器')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    args = parser.parse_args()
    
    run_server(args.port)