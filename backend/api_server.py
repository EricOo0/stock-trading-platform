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
from typing import Dict, List

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 添加agent目录到Python路径 (for utils.logging)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent'))

# 导入market_data_tool skill
from skills.market_data_tool.skill import main_handle
from skills.macro_data_tool.skill import MacroDataSkill
from skills.web_search_tool.skill import WebSearchSkill

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import mimetypes

class MarketDataAPIHandler(BaseHTTPRequestHandler):
    """市场数据API处理器"""
    
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
        elif path.startswith('/api/market/technical/'):
            self.handle_technical_analysis(path, query_params)
        elif path == '/api/web-search':
            self.handle_web_search(query_params)
        elif path.startswith('/api/financial-report/'):
            self.handle_financial_report(path)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/market-data':
            self.handle_market_data()
        elif path == '/api/financial/indicators':
            self.handle_financial_indicators()
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
            
            # 调用skill获取数据
            result = main_handle(query)
            logger.info(f"Skill返回结果: {json.dumps(result, default=str, ensure_ascii=False)}")
            
            # 处理skill返回的结果
            if result.get('status') == 'success' and result.get('data'):
                # 单个股票查询成功
                data = result.get('data')
                # 处理datetime对象
                if 'timestamp' in data and hasattr(data['timestamp'], 'isoformat'):
                    data['timestamp'] = data['timestamp'].isoformat()
                
                response = {
                    'status': 'success',
                    'symbol': result.get('symbol', ''),
                    'data': data,
                    'timestamp': result.get('timestamp', datetime.now().isoformat()),
                    'data_source': 'real',
                    'cache_hit': result.get('cache_hit', False),
                    'response_time_ms': result.get('response_time_ms', 0)
                }
            elif result.get('status') in ['partial', 'success'] and result.get('results'):
                # 批量查询结果，提取第一个成功的结果
                successful_results = [r for r in result.get('results', []) if r.get('status') == 'success']
                if successful_results:
                    first_result = successful_results[0]
                    data = first_result.get('data')
                    # 处理datetime对象
                    if data and 'timestamp' in data and hasattr(data['timestamp'], 'isoformat'):
                        data['timestamp'] = data['timestamp'].isoformat()
                    
                    response = {
                        'status': 'success',
                        'symbol': first_result.get('symbol', ''),
                        'data': data,
                        'timestamp': first_result.get('timestamp', datetime.now().isoformat()),
                        'data_source': 'real',
                        'cache_hit': first_result.get('cache_hit', False),
                        'response_time_ms': first_result.get('response_time_ms', 0)
                    }
                else:
                    # 没有成功的结果
                    failed_result = result.get('results', [{}])[0]
                    response = {
                        'status': 'error',
                        'symbol': query,
                        'message': failed_result.get('error_message', '查询失败'),
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'real',
                        'cache_hit': False,
                        'response_time_ms': 0
                    }
            else:
                # 查询失败
                response = {
                    'status': 'error',
                    'symbol': query,
                    'message': result.get('message', '查询失败'),
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'real',
                    'cache_hit': False,
                    'response_time_ms': 0
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
                    result = main_handle(f"获取{symbol}的行情数据")
                    if result.get('status') == 'success' and result.get('data'):
                        results.append(result['data'])
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
            from skills.market_data_tool.skill import MarketDataSkill
            skill = MarketDataSkill()
            
            # 获取历史数据
            result = skill.get_historical_data(symbol, period, '1d')
            
            # 处理结果
            if result.get('status') == 'success' and result.get('data'):
                # 限制返回的数据条数
                historical_data = result.get('data', [])[:count]
                
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
                    'message': result.get('message', '获取历史数据失败'),
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
            from skills.market_data_tool.skill import MarketDataSkill
            skill = MarketDataSkill()
            # 强制使用日线数据进行指标计算
            result = skill.get_historical_data(symbol, period, '1d')
            
            if result.get('status') != 'success' or not result.get('data'):
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'No data found'}).encode())
                return

            # 转换为DataFrame并计算指标
            import pandas as pd
            df = pd.DataFrame(result['data'])
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
            df = df.where(pd.notnull(df), None)
            
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
            web_search_skill = WebSearchSkill(
                tavily_api_key="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",
                search_kwargs={
                    "topic": "news",
                    "days": 7,
                    "max_results": 30
                }
            )
            
            # 执行搜索
            result = web_search_skill._run(query)
            
            if result.get('status') == 'success':
                response = {
                    'status': 'success',
                    'query': query,
                    'results': result.get('raw_results', []),  # Return structured array
                    'provider': result.get('provider', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
                self._set_headers(200)
            else:
                response = {
                    'status': 'error',
                    'message': result.get('message', '搜索失败'),
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
                
                from skills.financial_report_tool.skill import FinancialReportSkill
                skill = FinancialReportSkill()
                result = skill.analyze_report(symbol)
                
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
            from skills.financial_report_tool.skill import FinancialReportSkill
            
            skill = FinancialReportSkill()
            
            # 1. Get Metrics
            metrics_result = skill.get_financial_metrics(symbol)
            
            # 2. Get Latest Report Metadata
            report_result = skill.get_latest_report(symbol)
            
            response = {
                'status': 'success',
                'symbol': symbol,
                'metrics': metrics_result.get('metrics', []) if metrics_result.get('status') == 'success' else [],
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
        """处理财务指标请求 POST /api/financial/indicators"""
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
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': 'Symbol is required'
                }).encode())
                return
            
            logger.info(f"获取财务指标: {symbol}, years={years}, use_cache={use_cache}")
            
            # 导入财务报告skill
            from skills.financial_report_tool.skill import FinancialReportSkill
            
            skill = FinancialReportSkill()
            
            # 调用get_financial_indicators方法
            result = skill.get_financial_indicators(symbol, years=years, use_cache=use_cache)
            
            if result.get('status') == 'success':
                self._set_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False, default=str).encode())
            else:
                self._set_headers(200)  # 仍然返回200，但包含错误状态
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
                
        except Exception as e:
            logger.error(f"处理财务指标请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            error_response = {
                'status': 'error',
                'message': f'服务器错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self._set_headers(500)
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode())

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
            
            skill = MacroDataSkill()
            result = skill.get_historical_data(indicator, period)
            
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
def run_server(port=8000):
    """运行API服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MarketDataAPIHandler)
    logger.info(f"市场数据API服务器启动，端口: {port}")
    logger.info(f"API端点:")
    logger.info(f"  POST /api/market-data - 查询股票数据")
    logger.info(f"  POST /api/financial/indicators - 获取财务指标")
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