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

# 导入market_data_tool skill
from skills.market_data_tool.skill import main_handle
from skills.macro_data_tool.skill import MacroDataSkill

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        if path == '/api/market-data/hot':
            self.handle_hot_stocks()
        elif path.startswith('/api/market/historical/'):
            self.handle_historical_data(path, query_params)
        elif path.startswith('/api/macro-data/historical/'):
            self.handle_macro_historical_data(path, query_params)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/market-data':
            self.handle_market_data()
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
    logger.info(f"  GET  /api/market-data/hot - 获取热门股票")
    logger.info(f"  GET  /api/market/historical/<symbol> - 获取历史数据")
    
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