

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
from backend.infrastructure.config.loader import config
from typing import Dict, Any, Optional, List, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AkShareTool:
    """
    AkShare Tool
    Provides A-share market data, financial indicators, and China macro data.
    """

    def __init__(self):
        self._sector_mapping = {
            "IT服务": "互联网服务",
            "互联网电商": "互联网服务",
            "元件": "电子元件",
            "公路铁路运输": "铁路公路",
            "其他电子": "电子元件",
            "其他电源设备": "电源设备",
            "养殖业": "农牧饲渔",
            "军工电子": "航天航空",
            "军工装备": "航天航空",
            "农产品加工": "农牧饲渔",
            "农化制品": "化学制品",
            "包装印刷": "造纸印刷",
            "化学纤维": "化纤行业",
            "厨卫电器": "家电行业",
            "家居用品": "家用轻工",
            "小家电": "家电行业",
            "工业金属": "有色金属",
            "建筑材料": "装修建材",
            "建筑装饰": "装修装饰",
            "影视院线": "文化传媒",
            "房地产": "房地产开发",
            "旅游及酒店": "旅游酒店",
            "服装家纺": "纺织服装",
            "机场航运": "航空机场",
            "汽车服务及其他": "汽车服务",
            "油气开采及服务": "石油行业",
            "港口航运": "航运港口",
            "煤炭开采加工": "煤炭行业",
            "物流": "物流行业",
            "环保设备": "环保行业",
            "环境治理": "环保行业",
            "电力": "电力行业",
            "白色家电": "家电行业",
            "白酒": "酿酒行业",
            "石油加工贸易": "石油行业",
            "种植业与林业": "农牧饲渔",
            "纺织制造": "纺织服装",
            "综合": "综合行业",
            "自动化设备": "专用设备",
            "贸易": "贸易行业",
            "轨交设备": "交运设备",
            "造纸": "造纸印刷",
            "金属新材料": "有色金属",
            "钢铁": "钢铁行业",
            "零售": "商业百货",
            "食品加工制造": "食品饮料",
            "饮料制造": "食品饮料",
            "黑色家电": "家电行业",
        }

        self._concept_mapping = {
            "5G": "5G概念",
            "CRO概念": "CRO",
            "IP经济(谷子经济)": "谷子经济",
            "MR(混合现实)": "混合现实",
            "MicroLED概念": "MicroLED",
            "PCB概念": "PCB",
            "PEEK材料": "PEEK材料概念",
            "Sora概念(文生视频)": "Sora概念",
            "一体化压铸": "汽车一体化压铸",
            "上海自贸区": "上海自贸",
            "东数西算(算力)": "东数西算",
            "中字头股票": "中字头",
            "京津冀一体化": "京津冀",
            "人民币贬值受益": "贬值受益",
            "供销社": "供销社概念",
            "元宇宙": "元宇宙概念",
            "光刻机": "光刻机(胶)",
            "军工信息化": "军工",
            "华为海思概念股": "华为海思",
            "可降解塑料": "降解塑料",
            "同花顺中特估100": "中特估",
            #"同花顺新质50": "新质生产力", # Invalid board
            "国企改革": "央国企改革",
            "国资云": "国资云概念",
            "安防": "国家安防",
            "富士康概念": "富士康",
            "工业互联网": "工业互联",
            "新型烟草(电子烟)": "电子烟",
            "新股与次新股": "次新股",
            "新能源汽车": "新能源",
            "有机硅概念": "有机硅",
            "核电": "核能核电",
            "氟化工概念": "氟化工",
            "水利": "水利建设",
            "汽车拆解概念": "汽车拆解",
            "海南自贸区": "海南自贸",
            "煤化工概念": "煤化工",
            "特斯拉概念": "特斯拉",
            "独角兽概念": "独角兽",
            "猪肉": "猪肉概念",
            "电力物联网": "物联网",
            "电子纸": "电子纸概念",
            "白酒概念": "白酒",
            "知识产权保护": "知识产权",
            "禽流感": "流感",
            "科创次新股": "次新股",
            "细胞免疫治疗": "免疫治疗",
            "股权转让(并购重组)": "股权转让",
            "跨境支付(CIPS)": "跨境支付",
            "车联网(车路协同)": "车联网(车路云)",
            "钛白粉概念": "钛白粉",
            "锂电池概念": "锂电池",
            "预制菜": "预制菜概念",
            # Additional mappings from manual analysis
            "央企国企改革": "央国企改革",
            "上海国企改革": "上海国资",
            "深圳国企改革": "深圳国资",
            "化债概念(AMC概念)": "化债(AMC)概念",
            "2025年报预增": "年报预增",
            "HJT电池": "HJT电池", # Might be correct or HJT?
            "MCU芯片": "MCU芯片", # Likely match
            "NMN概念": "NMN概念",
            "ST板块": "ST板块",
            "TOPCON电池": "TOPCon电池", # Case sensitivity?
            "三胎概念": "三胎概念",
            "华为手机": "华为概念",
            "华为数字能源": "华为概念", # Fallback
            "华为盘古": "华为概念", # Fallback
            "华为鲲鹏": "华为概念", # Fallback
            "卫星导航": "北斗导航",
            "算力租赁": "算力概念",
            "金属铅": "基本金属",
            "金属锌": "基本金属",
            "金属铜": "基本金属",
            "金属钴": "小金属概念",
            "金属镍": "小金属概念",
            "智能医疗": "医疗器械", # Approx
            "数字乡村": "乡村振兴",
            "人脸识别": "机器视觉",
            "阿尔茨海默概念": "阿尔茨海默",
            "国产操作系统": "操作系统",
            "航空发动机": "航天航空",
            "光纤概念": "光通信模块",
            "智能音箱": "智能音箱",
            "赛马概念": "赛马概念",
            "互联网金融": "互联金融",
            "同花顺果指数": "苹果概念",
            "牙科医疗": "牙科医疗", # Should match?
            "猴痘概念": "猴痘概念",
            "横琴新区": "横琴概念",
            "俄乌冲突概念": "俄乌冲突",
            "语音技术": "语音技术",
            "无人零售": "新零售",
            "福建自贸区": "福建自贸",
            "共封装光学(CPO)": "CPO概念",
            "信托概念": "信托",
            "太赫兹": "太赫兹",
            "免税店": "免税概念",
            "足球概念": "体育产业",
            "广东自贸区": "广东自贸",
            "海峡两岸": "海峡西岸",
            "液冷服务器": "液冷概念",
            "国产航母": "航母概念",
            "智能座舱": "智能座舱",
            "网约车": "网约车",
            "摘帽": "摘帽",
            "同花顺出海50": "出海50", # Unlikely to match
            "高端装备": "高端装备",
            "毫米波雷达": "雷达",
            "丙烯酸": "丙烯酸",
            "露营经济": "露营经济",
        }

    # ========================== Unified API (New) ==========================
    # 下列函数为新一代统一接口，提供了跨市场自动路由、标准化的返回结构与增强的错误兜底。
    # 建议所有新业务逻辑优先调用以下接口。

    def get_indices_quote(self, market: str) -> List[Dict[str, Any]]:
        """
        [New] 批量获取市场核心指数行情 (Bulk Indices Quote)
        
        Args:
            market: 市场类型 'CN' (或 'A'), 'HK', 'US'
            
        Returns:
            List of index quotes
        """
        try:
            # Normalize market
            market = market.upper()
            if market == 'A': market = 'CN'
            
            results = []
            
            if market == 'CN':
                # Use get_a_share_indices_spot without target filter to get all key indices
                # get_a_share_indices_spot already uses "沪深重要指数" which covers what we need
                raw_data = self.get_a_share_indices_spot()
                
                # Filter for the specific list requested by user
                target_names = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]
                
                for item in raw_data:
                    name = str(item.get('名称', ''))
                    if name in target_names:
                        results.append({
                            "symbol": str(item.get('代码')),
                            "name": name,
                            "price": self._safe_get(item, '最新价'),
                            "open": self._safe_get(item, '今开'),
                            "high": self._safe_get(item, '最高'),
                            "low": self._safe_get(item, '最低'),
                            "prev_close": self._safe_get(item, '昨收'),
                            "change_pct": self._safe_get(item, '涨跌幅'),
                            "change_amount": self._safe_get(item, '涨跌额'),
                            "volume": self._safe_get(item, '成交量'),
                            "turnover": self._safe_get(item, '成交额'),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "market": "CN_INDEX",
                            "source": "akshare_index_spot"
                        })
                # Sort by order in target_names
                results.sort(key=lambda x: target_names.index(x['name']) if x['name'] in target_names else 999)
                
            elif market == 'HK':
                # HK Targets: HSI, HSTECH
                targets = [
                    {"symbol": "HSI", "name": "恒生指数"}, 
                    {"symbol": "HSTECH", "name": "恒生科技"}
                ]
                # Parallel fetch simulated by sequential loop (few items)
                for t in targets:
                    res = self.get_hk_index_latest(t["symbol"])
                    if "error" not in res:
                        results.append({
                            "symbol": t["symbol"],
                            "name": t["name"],
                            "price": self._safe_get(res, 'close'),
                            "open": self._safe_get(res, 'open'),
                            "high": self._safe_get(res, 'high'),
                            "low": self._safe_get(res, 'low'),
                            "volume": self._safe_get(res, 'volume'),
                            "change_pct": self._safe_get(res, 'change_pct'),
                            "timestamp": str(res.get('date', '')),
                            "market": "HK_INDEX",
                            "source": "sina_hk_index"
                        })
                        
            elif market == 'US':
                # US Targets: .IXIC, .DJI, .INX
                targets = [
                    {"symbol": ".IXIC", "name": "纳斯达克"}, 
                    {"symbol": ".DJI", "name": "道琼斯"}, 
                    {"symbol": ".INX", "name": "标普500"}
                ]
                for t in targets:
                    res = self.get_us_index_latest(t["symbol"])
                    if "error" not in res:
                        results.append({
                            "symbol": t["symbol"],
                            "name": t["name"],
                            "price": self._safe_get(res, 'close'),
                            "open": self._safe_get(res, 'open'),
                            "high": self._safe_get(res, 'high'),
                            "low": self._safe_get(res, 'low'),
                            "volume": self._safe_get(res, 'volume'),
                            "change_pct": self._safe_get(res, 'change_pct'),
                            "timestamp": str(res.get('date', '')),
                            "market": "US_INDEX",
                            "source": "sina_us_index"
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"get_indices_quote failed for {market}: {e}")
            return []

    def get_indices_history(self, market: str, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        [New] 批量获取核心指数历史行情 (Bulk Indices History)
        
        Args:
            market: 市场类型 'CN' (或 'A'), 'HK', 'US'
            days: 获取最近多少天的数据
            
        Returns:
            Dict: Key 为指数 symbol, Value 为历史数据列表
        """
        try:
            market = market.upper()
            if market == 'A': market = 'CN'
            
            results = {}
            import akshare as ak
            
            # Helper to process history dataframe
            def process_df(df, date_col='date', close_col='close', change_col='change_pct'):
                if df is None or df.empty: return []
                # Sort by date asc
                if date_col in df.columns:
                    df = df.sort_values(date_col)
                # Take last N days
                df = df.tail(days)
                
                hist = []
                for _, row in df.iterrows():
                    hist.append({
                        "date": str(row.get(date_col, "")),
                        "close": self._safe_get(row, close_col),
                        "change_pct": self._safe_get(row, change_col)
                    })
                return hist

            if market == 'CN':
                # Target symbols matching get_indices_quote
                # Mapping Name -> Code for akshare call
                # 上证指数: sh000001, 深证成指: sz399001, 创业板指: sz399006, 
                # 科创50: sh000688, 沪深300: sz399300, 中证500: sz399905, 北证50: bj899050
                targets = {
                    "000001": "sh000001", # 上证
                    "399001": "sz399001", # 深证
                    "399006": "sz399006", # 创业板
                    "000688": "sh000688", # 科创50
                    "000300": "sz399300", # 沪深300
                    "000905": "sz399905", # 中证500
                    "899050": "bj899050"  # 北证50
                }
                
                for simple_code, full_code in targets.items():
                    try:
                        df = ak.stock_zh_index_daily_em(symbol=full_code)
                        # Columns: date, open, close, high, low, volume, amount
                        # Need to calculate change_pct if not present? 
                        # stock_zh_index_daily_em does not return change_pct usually?
                        # It returns: date, open, close, high, low, volume, amount
                        # We can calc pct change.
                        if not df.empty:
                            df['change_pct'] = df['close'].pct_change() * 100
                            # Fill first NaN with 0 or previous close if available? For tail(7) it's fine.
                            results[simple_code] = process_df(df, 'date', 'close', 'change_pct')
                    except Exception as e:
                        logger.warning(f"Failed to get history for {simple_code}: {e}")

            elif market == 'HK':
                # HSI, HSTECH
                targets = ["HSI", "HSTECH"] 
                # Note: HSTECH might need specific symbol for sina. 
                # ak.stock_hk_index_daily_sina(symbol="HSI") works.
                # HSTECH symbol in Sina? Usually "HSTECH".
                
                for code in targets:
                    try:
                        df = ak.stock_hk_index_daily_sina(symbol=code)
                        # Columns: date, open, high, low, close, volume
                        if not df.empty:
                            df['change_pct'] = df['close'].pct_change() * 100
                            results[code] = process_df(df, 'date', 'close', 'change_pct')
                    except Exception as e:
                        logger.warning(f"Failed to get history for {code}: {e}")

            elif market == 'US':
                # .IXIC, .DJI, .INX
                targets = [".IXIC", ".DJI", ".INX"]
                
                for code in targets:
                    try:
                        df = ak.index_us_stock_sina(symbol=code)
                        # Columns: date, open, high, low, close, volume
                        if not df.empty:
                            df['change_pct'] = df['close'].pct_change() * 100
                            results[code] = process_df(df, 'date', 'close', 'change_pct')
                    except Exception as e:
                        logger.warning(f"Failed to get history for {code}: {e}")
            
            return results

        except Exception as e:
            logger.error(f"get_indices_history failed for {market}: {e}")
            return {}


    def get_market_turnover(self, market: str = "CN", start_date: Optional[str] = None, end_date: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        [New] 获取全市场总成交额 (Total Market Turnover)
        
        支持实时快照（不传日期）和历史区间（传日期）。
        目前主要支持 'CN' (A股)，通过计算“上证指数成交额 + 深证成指成交额”估算。
        
        Args:
            market: 'CN' (default)
            start_date: 开始日期 YYYYMMDD (e.g. "20240101")
            end_date: 结束日期 YYYYMMDD (e.g. "20240110")
            
        Returns:
            - If dates provided: List[Dict] with historical turnover
            - If no dates: Dict with realtime snapshot
        """
        try:
            market = market.upper()
            if market == 'A': market = 'CN'
            
            if market != 'CN':
                return {"error": f"Market turnover not supported for {market}"}

            import akshare as ak

            # 1. Real-time Snapshot (No dates provided)
            if not start_date and not end_date:
                df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
                if df.empty: return {"error": "Index data unavailable"}
                
                sh_row = df[df['名称'] == '上证指数']
                sz_row = df[df['名称'] == '深证成指']
                
                sh_val = float(sh_row.iloc[0]['成交额']) if not sh_row.empty else 0.0
                sz_val = float(sz_row.iloc[0]['成交额']) if not sz_row.empty else 0.0
                
                total = sh_val + sz_val
                display = f"{total/100000000:.2f}亿"
                if total > 1000000000000:
                    display = f"{total/1000000000000:.2f}万亿"
                    
                return {
                    "turnover": total,
                    "turnover_display": display,
                    "sh_turnover": sh_val,
                    "sz_turnover": sz_val,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # 2. Historical Data (Dates provided)
            else:
                # Default dates if partially missing
                if not start_date: start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                if not end_date: end_date = datetime.now().strftime("%Y%m%d")
                
                # Fetch history for SH and SZ
                # sh000001, sz399001
                df_sh = ak.stock_zh_index_daily_em(symbol="sh000001")
                df_sz = ak.stock_zh_index_daily_em(symbol="sz399001")
                
                if df_sh.empty or df_sz.empty:
                    return []
                
                # Filter by date range
                # Date in df is YYYY-MM-DD string or datetime? stock_zh_index_daily_em usually string YYYY-MM-DD
                # Convert input YYYYMMDD to YYYY-MM-DD
                s_date_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
                e_date_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
                
                # Filter helper
                def filter_df(d):
                    return d[(d['date'] >= s_date_fmt) & (d['date'] <= e_date_fmt)].copy()
                
                df_sh_sub = filter_df(df_sh)[['date', 'amount']]
                df_sz_sub = filter_df(df_sz)[['date', 'amount']]
                
                # Rename for merge
                df_sh_sub.rename(columns={'amount': 'sh_amount'}, inplace=True)
                df_sz_sub.rename(columns={'amount': 'sz_amount'}, inplace=True)
                
                # Merge
                merged = pd.merge(df_sh_sub, df_sz_sub, on='date', how='inner')
                merged['total'] = merged['sh_amount'] + merged['sz_amount']
                
                results = []
                for _, row in merged.iterrows():
                    results.append({
                        "date": row['date'],
                        "turnover": float(row['total']),
                        "sh_turnover": float(row['sh_amount']),
                        "sz_turnover": float(row['sz_amount'])
                    })
                
                # Sort descending (newest first)
                results.sort(key=lambda x: x['date'], reverse=True)
                return results
            
        except Exception as e:
            logger.error(f"get_market_turnover failed: {e}")
            return {"error": str(e)}


    def get_index_quote(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        [废弃] 获取指数实时行情 (Unified Index Quote)，使用 get_indices_quote 批量获取。
        
        Args:
            symbol: 指数代码或名称 (e.g. '000001', '上证指数', '.DJI', 'HSI')
            market: 可选市场类型 'CN', 'HK', 'US'。若为 None 则自动探测。
        """
        try:
            # 1. Detect Market if not provided
            if not market:
                if symbol.startswith("."): market = 'US'
                elif symbol in ["HSI", "HSTECH"]: market = 'HK'
                # Common CN index names or codes
                elif symbol in ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]: market = 'CN'
                elif symbol.isdigit() and len(symbol) == 6: market = 'CN' # Ambiguous but likely CN
                else: market = 'CN' # Default to CN for unknown

            if market == 'CN' or market == 'CN_INDEX':
                # Use legacy get_a_share_indices_spot which now supports codes or names
                res_list = self.get_a_share_indices_spot([symbol])
                if not res_list:
                    return {"error": f"CN Index not found: {symbol}"}
                
                item = res_list[0]
                return {
                    "symbol": str(item.get('代码')),
                    "name": str(item.get('名称')),
                    "price": self._safe_get(item, '最新价'),
                    "open": self._safe_get(item, '今开'),
                    "high": self._safe_get(item, '最高'),
                    "low": self._safe_get(item, '最低'),
                    "prev_close": self._safe_get(item, '昨收'),
                    "change_pct": self._safe_get(item, '涨跌幅'),
                    "change_amount": self._safe_get(item, '涨跌额'),
                    "volume": self._safe_get(item, '成交量'),
                    "turnover": self._safe_get(item, '成交额'),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market": "CN_INDEX",
                    "source": "akshare_index_spot"
                }

            elif market == 'HK' or market == 'HK_INDEX':
                res = self.get_hk_index_latest(symbol)
                if "error" in res: return res
                return {
                    "symbol": symbol,
                    "name": res.get("name", symbol),
                    "price": self._safe_get(res, 'close'),
                    "open": self._safe_get(res, 'open'),
                    "high": self._safe_get(res, 'high'),
                    "low": self._safe_get(res, 'low'),
                    "volume": self._safe_get(res, 'volume'),
                    "timestamp": str(res.get('date', '')),
                    "market": "HK_INDEX",
                    "source": "sina_hk_index"
                }

            elif market == 'US' or market == 'US_INDEX':
                res = self.get_us_index_latest(symbol)
                if "error" in res: return res
                return {
                    "symbol": symbol,
                    "name": res.get("name", symbol),
                    "price": self._safe_get(res, 'close'),
                    "open": self._safe_get(res, 'open'),
                    "high": self._safe_get(res, 'high'),
                    "low": self._safe_get(res, 'low'),
                    "volume": self._safe_get(res, 'volume'),
                    "timestamp": str(res.get('date', '')),
                    "market": "US_INDEX",
                    "source": "sina_us_index"
                }
            
            return {"error": f"Unknown index market: {market}"}

        except Exception as e:
            logger.error(f"get_index_quote failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def get_quote(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        [New] 获取全市场标的实时行情 (Unified Real-time Quote)
        自动识别 A股/港股/美股/ETF，并返回标准化字段。

        Args:
            symbol: 代码 (e.g., '600036', '00700', 'AAPL', '510300')
            market: 可选市场类型 'A', 'HK', 'US', 'ETF'。若为 None 则自动探测。

        Returns:
            Dict containing standardized fields:
            - symbol, name, market (str)
            - price (float): 当前价
            - open, high, low, prev_close (float)
            - change_pct (float): 涨跌幅 % (e.g. 1.50)
            - change_amount (float): 涨跌额
            - volume (float): 成交量 (股/份)
            - turnover (float): 成交额 (元)
            - turnover_rate (float): 换手率 %
            - pe (float, optional): 动态市盈率
            - pb (float, optional): 市净率
            - market_cap (float, optional): 总市值
            - timestamp (str): 数据时间 (YYYY-MM-DD HH:MM:SS)
        """
        try:
            # 1. Detect Market
            if not market:
                market = self._detect_market_type(symbol)

            # 2. Route to specific logic
            if market == 'ETF':
                # Try ETF first
                try:
                    return self._get_etf_quote(symbol)
                except:
                    # Fallback to stock if ETF fails (maybe it's a LOF treated as A-share)
                    market = 'A'

            if market == 'A':
                # Reuse existing robust logic but wrap it
                # existing get_stock_quote has detailed implementation
                # We can call it directly as it returns the right structure mostly
                res = self.get_stock_quote(symbol)
                if "error" in res:
                    return res
                # Standardize keys if needed (current get_stock_quote uses standardized keys already)
                # Just ensure 'price' is present (it uses 'current_price')
                res['price'] = res.get('current_price')
                return res

            elif market == 'HK':
                # Use dedicated HK method
                return self._get_hk_quote_detail(symbol)

            elif market == 'US':
                # Use dedicated US method
                return self._get_us_quote_detail(symbol)
                
            # Removed index routing from get_quote as per user request
            # elif market in ['CN_INDEX', 'HK_INDEX', 'US_INDEX']:
            #     # Route to index quote
            #     return self.get_index_quote(symbol, market=market)

            else:
                return {"error": f"Unknown market for symbol {symbol}"}

        except Exception as e:
            logger.error(f"get_quote failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def get_history(self,
                    symbol: str,
                    period: str = "daily",
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    adjust: str = "qfq") -> List[Dict[str, Any]]:
        """
        [New] 获取全市场历史行情 (Unified Historical K-Line)
        """
        try:
            market = self._detect_market_type(symbol)

            # Map period to akshare params
            # AkShare usually takes 'daily', 'weekly', 'monthly'
            # For A-share: stock_zh_a_hist(period='daily'/'weekly'/'monthly')
            # For HK: stock_hk_hist(period='daily'...)
            # For US: stock_us_hist(period='daily'...)

            ak_period = "daily"
            if period in ["weekly", "week", "1w"]: ak_period = "weekly"
            elif period in ["monthly", "month", "1mo"]: ak_period = "monthly"

            # Date handling
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                # Default 1 year if not provided
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            df = pd.DataFrame()

            if market == 'A' or market == 'ETF':
                # ETF also uses stock_zh_a_hist often, or fund_etf_hist_em
                if market == 'ETF':
                    try:
                        df = ak.fund_etf_hist_em(symbol=symbol, period=ak_period, start_date=start_date, end_date=end_date, adjust=adjust)
                    except:
                        # Fallback to stock interface
                        df = ak.stock_zh_a_hist(symbol=symbol, period=ak_period, start_date=start_date, end_date=end_date, adjust=adjust)
                else:
                    df = ak.stock_zh_a_hist(symbol=symbol, period=ak_period, start_date=start_date, end_date=end_date, adjust=adjust)

            elif market == 'HK':
                # stock_hk_hist(symbol='00700', period='daily', start_date='...', end_date='...', adjust='qfq')
                df = ak.stock_hk_hist(symbol=symbol, period=ak_period, start_date=start_date, end_date=end_date, adjust=adjust)

            elif market == 'US':
                # Use stock_us_daily (Sina source) which handles symbols like 'AAPL' without prefix
                try:
                    df = ak.stock_us_daily(symbol=symbol, adjust=adjust)
                except Exception as e:
                    logger.warning(f"stock_us_daily failed for {symbol}: {e}")
                    df = pd.DataFrame()

            if df is None or df.empty:
                return []

            # Standardize columns
            # Common: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 涨跌幅...
            res = []
            for _, row in df.iterrows():
                item = {
                    "date": str(row.get('日期', '')),
                    "open": self._safe_get(row, '开盘'),
                    "close": self._safe_get(row, '收盘'),
                    "high": self._safe_get(row, '最高'),
                    "low": self._safe_get(row, '最低'),
                    "volume": self._safe_get(row, '成交量'),
                    "turnover": self._safe_get(row, '成交额'),
                    "pct_change": self._safe_get(row, '涨跌幅')
                }
                res.append(item)
            return res

        except Exception as e:
            logger.error(f"get_history failed: {e}")
            return []

    def get_fund_flow(self, target: str, flow_type: str = "stock") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        [New] 获取资金流向数据 (Unified Fund Flow)
        """
        try:
            if flow_type == 'stock':
                return self.get_stock_fund_flow(target)

            elif flow_type == 'north':
                # 北向资金: stock_hsgt_hist_em(symbol="北向资金")
                # 原接口 stock_hsgt_north_net_flow_in_em 已失效
                df = ak.stock_hsgt_hist_em(symbol="北向资金")
                if df.empty: return []
                
                res = []
                for _, row in df.iterrows():
                    # stock_hsgt_hist_em returns '日期', '当日成交净买额', '买入成交额', '卖出成交额'
                    res.append({
                        "date": str(row['日期']),
                        "value": self._safe_get(row, '当日成交净买额'),
                        "buy_amount": self._safe_get(row, '买入成交额'),
                        "sell_amount": self._safe_get(row, '卖出成交额')
                    })
                # Sort desc
                res.sort(key=lambda x: x['date'], reverse=True)
                return res

            elif flow_type == 'south':
                # 南向资金: stock_hsgt_hist_em(symbol="南向资金")
                df = ak.stock_hsgt_hist_em(symbol="南向资金")
                if df.empty: return []
                res = []
                for _, row in df.iterrows():
                    res.append({
                        "date": str(row['日期']),
                        "value": self._safe_get(row, '当日成交净买额'),
                        "buy_amount": self._safe_get(row, '买入成交额'),
                        "sell_amount": self._safe_get(row, '卖出成交额')
                    })
                # Sort desc
                res.sort(key=lambda x: x['date'], reverse=True)
                return res

            elif flow_type == 'sector':
                # Individual sector flow?
                # AkShare has stock_fund_flow_industry(symbol='行业名')?
                # Actually stock_fund_flow_industry returns rank.
                # Specific sector daily flow: stock_sector_fund_flow_rank? No.
                # For now return empty or implement later.
                return []

            return []
        except Exception as e:
            logger.error(f"get_fund_flow failed: {e}")
            return []

    def get_board_info(self, board_name: str = "all", board_type: str = "industry", info_type: str = "rank") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        [New] 获取板块/概念深度信息 (Sector/Concept Board Info)
        """
        try:
            if info_type == 'rank':
                if board_type == 'concept':
                    return self.get_concept_fund_flow_rank()
                else:
                    return self.get_sector_fund_flow_rank()

            elif info_type == 'cons':
                if board_type == 'concept':
                    return self.get_concept_components(board_name)
                else:
                    return self.get_sector_components(board_name)

            return []
        except Exception as e:
            logger.error(f"get_board_info failed: {e}")
            return []

    def get_financials(self, symbol: str, report_type: str = "indicator") -> Dict[str, Any]:
        """
        [New] 获取基本面/财务数据 (Unified Fundamentals)
        """
        # Currently only supporting 'indicator' which wraps get_financial_indicators
        if report_type == 'indicator':
            return self.get_financial_indicators(symbol)
        return {}

    def get_macro(self, indicator: str, history: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        [New] 获取宏观经济数据 (Unified Macro Data)
        """
        if history:
            return self.get_macro_history(indicator)
        else:
            return self.get_macro_data(indicator)

    # --- Internal Helpers for New APIs ---

    def _detect_market_type(self, symbol: str) -> str:
        """Detect market type from symbol."""
        # US Index (common convention, e.g. .DJI)
        if symbol.startswith("."): return 'US_INDEX'
        
        # HK Index (common symbols)
        if symbol in ["HSI", "HSTECH"]: return 'HK_INDEX'
        
        # CN Index (common names)
        if symbol in ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]: return 'CN_INDEX'

        if symbol.startswith(("sh", "sz", "bj")): return 'A'
        if symbol.isdigit():
            if len(symbol) == 6:
                if symbol.startswith(("51", "159", "56", "58", "16")): return 'ETF'
                if symbol.startswith(("60", "00", "30", "68", "8", "4")): return 'A'
            if len(symbol) == 5: return 'HK' # 00700
        # Common US symbols are letters
        if symbol.isalpha(): return 'US'
        return 'A' # Default

    def _get_hk_quote_detail(self, symbol: str) -> Dict[str, Any]:
        """Get HK quote using stock_hk_spot_em or hist_min."""
        # stock_hk_spot_em gets ALL stocks. Too slow.
        # stock_hk_hist_min_em?
        try:
            # Clean symbol: remove 'hk' prefix if any
            code = symbol.replace("hk", "").replace("HK", "")
            # Try min data for latest price
            df = ak.stock_hk_hist_min_em(symbol=code, period="1", adjust="qfq")
            if df.empty: return {}
            row = df.iloc[-1]
            return {
                "symbol": symbol,
                "price": float(row['收盘']),
                "open": float(row['开盘']),
                "high": float(row['最高']),
                "low": float(row['最低']),
                "volume": float(row['成交量']),
                "turnover": float(row['成交额']),
                "change_pct": 0.0, # Min data usually doesn't have change pct relative to prev close
                "timestamp": str(row['时间']),
                "market": "HK"
            }
        except Exception as e:
            logger.error(f"HK quote failed: {e}")
            return {"error": str(e)}

    def _get_us_quote_detail(self, symbol: str) -> Dict[str, Any]:
        """Get US quote."""
        try:
            # 1. Try Sina Index Interface (Fast & Realtime for Indices)
            import akshare as ak
            df = ak.index_us_stock_sina(symbol=symbol)
            if not df.empty:
                # Calculate change pct if not present in the last row
                # ak.index_us_stock_sina returns historical data
                latest = df.iloc[-1]
                change_pct = 0.0
                
                if len(df) >= 2:
                    prev = df.iloc[-2]
                    prev_close = float(prev['close'])
                    curr_close = float(latest['close'])
                    if prev_close > 0:
                        change_pct = ((curr_close - prev_close) / prev_close) * 100
                
                return {
                    "symbol": symbol,
                    "price": self._safe_get(latest, 'close'),
                    "open": self._safe_get(latest, 'open'),
                    "high": self._safe_get(latest, 'high'),
                    "low": self._safe_get(latest, 'low'),
                    "volume": self._safe_get(latest, 'volume'),
                    "turnover": 0.0,
                    "change_pct": round(change_pct, 2),
                    "timestamp": str(latest.get('date', '')),
                    "market": "US"
                }
        except Exception as e:
            logger.debug(f"US Index quote failed for {symbol}: {e}")

        try:
            # Fallback or other methods for individual stocks?
            return {"error": "US Stock quote not fully implemented in AkShareTool, use Yahoo fallback"}
        except Exception:
            return {}

    # ========================== 以下函数准备逐步废弃 ==========================
    # ========================== Market Data (Legacy) ==========================

    def get_a_share_indices_spot(self, target_indices: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get A-share key indices latest spot data.
        Recommended to use get_quote() or get_board_info() instead.
        """
        try:
            import akshare as ak
            df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
            
            if df.empty:
                return []
            
            if target_indices:
                mask = df["名称"].isin(target_indices) | df["代码"].isin(target_indices)
                filtered = df[mask]
            else:
                targets = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]
                filtered = df[df["名称"].isin(targets)]
                
            return filtered.to_dict(orient="records")
        except Exception as e:
            logger.error(f"AkShare get_a_share_indices_spot failed: {e}")
            return []

    def get_hk_index_latest(self, symbol: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        [Deprecated] Get latest HK index quote via sina daily interface.
        Please use get_quote() instead.
        """
        try:
            import akshare as ak
            df = ak.stock_hk_index_daily_sina(symbol=symbol)
            if df.empty:
                return {}
            
            latest = df.iloc[-1].to_dict()
            change_pct = 0.0
            
            if len(df) >= 2:
                prev = df.iloc[-2]
                prev_close = float(prev['close'])
                curr_close = float(latest['close'])
                if prev_close > 0:
                    change_pct = ((curr_close - prev_close) / prev_close) * 100
            
            latest["change_pct"] = round(change_pct, 2)
            
            if name:
                latest["name"] = name
            return latest
        except Exception as e:
            logger.error(f"AkShare get_hk_index_latest failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def get_us_index_latest(self, symbol: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        [Deprecated] Get latest US index quote via sina interface.
        Please use get_quote() instead.
        """
        try:
            import akshare as ak
            df = ak.index_us_stock_sina(symbol=symbol)
            if df.empty:
                return {}
            
            latest = df.iloc[-1].to_dict()
            change_pct = 0.0
            
            if len(df) >= 2:
                prev = df.iloc[-2]
                prev_close = float(prev['close'])
                curr_close = float(latest['close'])
                if prev_close > 0:
                    change_pct = ((curr_close - prev_close) / prev_close) * 100
            
            latest["change_pct"] = round(change_pct, 2)
            
            if name:
                latest["name"] = name
            return latest
        except Exception as e:
            logger.error(f"AkShare get_us_index_latest failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def _is_likely_etf(self, symbol: str) -> bool:
        """Check if symbol looks like an ETF."""
        return symbol.startswith(("51", "159", "56", "58", "16"))

    def _get_etf_quote(self, symbol: str) -> Dict[str, Any]:
        """Get ETF real-time quote."""
        # 1. Min data for realtime price
        df_min = ak.fund_etf_hist_min_em(symbol=symbol, period="1", adjust="qfq")
        if df_min.empty:
            raise ValueError("ETF min data unavailable")

        latest_min = df_min.iloc[-1]
        current_price = float(latest_min['收盘'])
        timestamp = str(latest_min['时间'])

        # 2. Daily data
        today_str = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        df_daily = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=today_str, adjust="qfq")

        day_open = 0.0
        day_high = 0.0
        day_low = 0.0
        prev_close = 0.0
        volume = 0.0
        turnover = 0.0
        turnover_rate = 0.0
        change_percent = 0.0
        change_amount = 0.0

        if not df_daily.empty:
            latest_daily = df_daily.iloc[-1]
            min_date_part = timestamp.split(' ')[0]
            daily_date_str = str(latest_daily['日期'])

            if min_date_part == daily_date_str:
                day_open = float(latest_daily['开盘'])
                day_high = float(latest_daily['最高'])
                day_low = float(latest_daily['最低'])
                volume = float(latest_daily['成交量'])
                turnover = float(latest_daily['成交额'])
                turnover_rate = float(latest_daily['换手率'])
                change_percent = float(latest_daily['涨跌幅'])
                change_amount = float(latest_daily['涨跌额'])
                prev_close = float(latest_daily['收盘']) - change_amount
            else:
                prev_close = float(latest_daily['收盘'])
                day_open = float(latest_min['开盘'])

        return {
            "symbol": symbol,
            "current_price": current_price,
            "open": day_open,
            "high": day_high,
            "low": day_low,
            "prev_close": round(prev_close, 3),
            "change_amount": round(change_amount, 3),
            "change_percent": round(change_percent, 2),
            "volume": volume,
            "turnover": turnover,
            "turnover_rate": turnover_rate,
            "pe": None,
            "pb": None,
            "market_cap": None,
            "circulating_market_cap": None,
            "timestamp": timestamp,
            "market": "CN-ETF",
            "source": "akshare_etf"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        [Deprecated] Get real-time stock quote for A-shares using lightweight interfaces.
        Please use get_quote() instead.
        """
        if not self._validate_symbol(symbol):
            return {"error": "Invalid A-share symbol"}

        # Try ETF logic first for likely ETFs
        if self._is_likely_etf(symbol):
            try:
                return self._get_etf_quote(symbol)
            except Exception as e:
                logger.warning(f"ETF quote failed for {symbol}, falling back to stock quote: {e}")

        try:
            # 1. Market Data (Price, Volume, etc.)
            # Use 1-min kline for realtime price to avoid full market scan
            df_min = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="qfq")

            if df_min is None or df_min.empty: # Check for None explicitly
                raise ValueError("Market data unavailable (None or empty)")

            latest_min = df_min.iloc[-1]
            current_price = float(latest_min['收盘'])
            timestamp = str(latest_min['时间'])

            # Get Daily Data for Open/High/Low/PrevClose/TurnoverRate
            # Fetch last few days to handle holidays or market opening
            today_str = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

            df_daily = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=today_str, adjust="qfq")

            # Init defaults
            day_open = 0.0
            day_high = 0.0
            day_low = 0.0
            prev_close = 0.0
            volume = 0.0
            turnover = 0.0
            turnover_rate = 0.0
            change_percent = 0.0
            change_amount = 0.0

            if df_daily is not None and not df_daily.empty:
                latest_daily = df_daily.iloc[-1]
                # Check date match to ensure daily data is for the same day as min data
                min_date_part = timestamp.split(' ')[0]
                daily_date_str = str(latest_daily['日期'])

                if min_date_part == daily_date_str:
                    day_open = float(latest_daily['开盘'])
                    day_high = float(latest_daily['最高'])
                    day_low = float(latest_daily['最低'])
                    volume = float(latest_daily['成交量'])
                    turnover = float(latest_daily['成交额'])
                    turnover_rate = float(latest_daily['换手率'])
                    change_percent = float(latest_daily['涨跌幅'])
                    change_amount = float(latest_daily['涨跌额'])

                    # Calculated prev_close
                    # Note: stock_zh_a_hist close is today's close. prev_close = close - change_amount
                    prev_close = float(latest_daily['收盘']) - change_amount
                else:
                    # Daily data likely lagging (e.g. before daily close update), use latest daily as previous day
                    prev_close = float(latest_daily['收盘'])
                    # For open/high/low of TODAY, we might need to rely on Min data aggregation if Daily is not up-to-date
                    # But usually stock_zh_a_hist is updated reasonably fast.
                    # If mismatch, it means today's daily record isn't there yet.
                    # We can use min data for open/high/low/close approximation
                    day_open = float(latest_min['开盘']) # This is min open, inaccurate for day open
                    # Better fallback: use yesterday's close as prev_close
                    pass

            # 2. Valuation & Info (PE/PB/MarketCap)
            pe = None
            pb = None
            market_cap = None
            circulating_market_cap = None

            # Market Cap
            try:
                df_info = ak.stock_individual_info_em(symbol=symbol)
                if df_info is not None and not df_info.empty:
                    info_map = dict(zip(df_info['item'], df_info['value']))
                    market_cap = self._parse_float(info_map.get('总市值'))
                    circulating_market_cap = self._parse_float(info_map.get('流通市值'))
            except Exception as e:
                logger.warning(f"Failed to fetch stock info for {symbol}: {e}")

            # PE/PB Calculation
            try:
                df_fin = ak.stock_financial_abstract(symbol=symbol)
                if df_fin is not None and not df_fin.empty:
                    pe, pb = self._calculate_valuation(df_fin, current_price)
            except (TypeError, AttributeError, ValueError):
                # Common for indices or funds which don't have financial abstract
                logger.debug(f"Valuation data unavailable for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to calculate valuation for {symbol}: {e}")

            return {
                "symbol": symbol,
                "current_price": current_price,
                "open": day_open,
                "high": day_high,
                "low": day_low,
                "prev_close": round(prev_close, 2),
                "change_amount": round(change_amount, 2),
                "change_percent": round(change_percent, 2),
                "volume": volume,
                "turnover": turnover,
                "turnover_rate": turnover_rate,
                "pe": pe,
                "pb": pb,
                "market_cap": market_cap,
                "circulating_market_cap": circulating_market_cap,
                "timestamp": timestamp,
                "market": "A-share",
                "source": "akshare_combined"
            }
        except Exception as e:
            # Fallback: if it wasn't identified as ETF but stock fetch failed, try ETF
            if not self._is_likely_etf(symbol):
                try:
                    logger.info(f"Stock quote failed, retrying as ETF for {symbol}")
                    return self._get_etf_quote(symbol)
                except Exception as etf_e:
                    logger.debug(f"Fallback ETF quote also failed: {etf_e}")

            logger.error(f"AkShare get_stock_quote failed for {symbol}: {e}")
            return {"error": str(e)}

    def _calculate_valuation(self, df_fin: pd.DataFrame, price: float) -> tuple:
        """Calculate PE (TTM) and PB based on financial abstract."""
        # df_fin columns: '指标', '20250930', '20250630', ...
        # Find latest report date
        date_cols = [c for c in df_fin.columns if c.isdigit()]
        date_cols.sort(reverse=True)
        if not date_cols:
            return None, None

        latest_date = date_cols[0]

        # Helper to get value
        def get_val(metric):
            row = df_fin[df_fin['指标'] == metric]
            if row.empty: return None
            val = row.iloc[0].get(latest_date)
            try: return float(val)
            except: return None

        eps = get_val('基本每股收益')
        bps = get_val('每股净资产')

        pe = None
        pb = None

        if eps and eps != 0:
            # Simple TTM estimation:
            # If Q3 (0930), EPS_TTM ~= EPS / 3 * 4
            # If Q4 (1231), EPS_TTM = EPS
            # If Q1 (0331), EPS_TTM ~= EPS * 4
            month = int(latest_date[4:6])
            if month == 3: factor = 4.0
            elif month == 6: factor = 2.0
            elif month == 9: factor = 1.333
            else: factor = 1.0

            eps_ttm = eps * factor
            pe = round(price / eps_ttm, 2)

        if bps and bps != 0:
            pb = round(price / bps, 2)

        return pe, pb

    def _parse_float(self, val):
        if pd.isna(val): return None
        try: return float(val)
        except: return None


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_history(self, symbol: str, period: str = "30d") -> List[Dict[str, Any]]:
        """
        [Deprecated] Get historical data for A-shares.
        Please use get_history() instead.
        """
        if not self._validate_symbol(symbol): return []

        try:
            days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "ytd": 365, "max": 3650}
            if period.endswith('d') and period[:-1].isdigit():
                delta_days = int(period[:-1])
            else:
                delta_days = days_map.get(period, 30)

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=delta_days + 20)).strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")

            if df.empty: return []

            history = []
            for _, row in df.iterrows():
                history.append({
                    'timestamp': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': float(row['成交量'])
                })
            return history
        except Exception as e:
            logger.error(f"AkShare get_stock_history failed for {symbol}: {e}")
            return []

    def get_historical_data(self, symbol: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """Alias for get_stock_history to match SinaFinanceTool interface."""
        # AkShare mostly supports daily, ignore interval for now or map it
        return self.get_stock_history(symbol, period)

    # ========================== Financial Data ==========================

    def get_financial_indicators(self, symbol: str, years: int = 3) -> Dict[str, Any]:
        """
        [Deprecated] Get financial indicators for A-shares.
        Please use get_financials() instead.
        """
        try:
            # Try primary source first
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df.empty or len(df) < 2 or (df.iloc[0].get('日期') == '1900-01-01' and len(df) == 1):
                # Fallback to abstract if empty or insufficient
                logger.info(f"Primary financial indicators empty for {symbol}, trying abstract...")
                return self._get_indicators_from_abstract(symbol, years)

            # AkShare data is reversed (oldest first)
            df = df.iloc[::-1].reset_index(drop=True)
            df = df.head(years * 4 + 1)

            # Skip invalid execution row if any
            if df.iloc[0].get('日期') == '1900-01-01':
                df = df.iloc[1:].reset_index(drop=True)

            return {
                "revenue": self._extract_revenue(df),
                "profit": self._extract_profit(df),
                "cashflow": self._extract_cashflow(df),
                "debt": self._extract_debt(df),
                "shareholder_return": self._extract_shareholder_return(df),
                "history": self._extract_financial_history(df)
            }
        except Exception as e:
            logger.error(f"AkShare get_financial_indicators failed: {e}")
            # Try abstract as backup for exceptions too
            try:
                return self._get_indicators_from_abstract(symbol, years)
            except:
                return self._empty_indicators()

    def _get_indicators_from_abstract(self, symbol: str, years: int = 3) -> Dict[str, Any]:
        """Fallback method using stock_financial_abstract."""
        try:
            df = ak.stock_financial_abstract(symbol=symbol)
            if df.empty: return self._empty_indicators()

            # 1. Transpose: Set '指标' as index and transpose
            # Columns are dates, rows are metrics
            # Filter columns that look like dates
            date_cols = [c for c in df.columns if c.isdigit() and len(c) == 8]
            date_cols.sort(reverse=True) # Newest first

            # Limit to requested years (approx 4 quarters per year)
            limit = years * 4 + 1
            selected_dates = date_cols[:limit]

            if not selected_dates: return self._empty_indicators()

            # Extract metrics into a more usable structure
            # We need a DataFrame where rows = dates, cols = metrics
            # df has '指标' column.

            # Helper to get series for a metric
            def get_series(metric_name):
                row = df[df['指标'] == metric_name]
                if row.empty: return pd.Series(0, index=selected_dates)
                # Return data for selected dates
                return row.iloc[0][selected_dates].apply(lambda x: float(x) if x else 0.0)

            # Build a new DataFrame with dates as rows
            new_df = pd.DataFrame(index=selected_dates)
            new_df['日期'] = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in selected_dates]

            # Map metrics
            # Revenue
            new_df['主营业务收入增长率(%)'] = get_series('营业总收入增长率') * 100 # Abstract usually is decimal? Need verify.
            # Abstract values: 20250930: 7.57e8. Growth rates?
            # Abstract usually has '营业总收入增长率'. Let's check sample.
            # No sample for growth rate, but usually percentages in akshare are raw numbers or %.
            # Assuming raw decimal or percent. Safe check later.

            # Actually let's just extract what we need for the _extract_* helpers
            # _extract_revenue needs: '主营业务收入增长率(%)', '主营利润比重', '每股经营性现金流(元)'
            # _extract_profit needs: '扣除非经常性损益后的每股收益(元)', '销售毛利率(%)', '销售净利率(%)'
            # _extract_cashflow needs: '每股经营性现金流(元)', '每股收益_调整后(元)'
            # _extract_debt needs: '资产负债率(%)', '流动比率'
            # _extract_shareholder_return needs: '股息发放率(%)', '净资产收益率(%)'

            # Mapping Abstract Indicators to Helper Keys
            mapping = {
                '主营业务收入增长率(%)': '营业总收入增长率', # Note: Abstract might be '营业总收入同比增长(%)' or similar.
                # From inspect: '营业总收入增长率'.
                '每股经营性现金流(元)': '每股经营现金流',
                '扣除非经常性损益后的每股收益(元)': '扣非净利润', # Approx? No, abstract has '基本每股收益' and maybe '扣非每股收益'?
                # Abstract has '扣非净利润' (Total). We can calc per share or just use Total if helper adapted.
                # Actually helper uses '每股...'. Abstract has '基本每股收益'.
                # Let's map to what we have.
                '销售毛利率(%)': '毛利率',
                '销售净利率(%)': '销售净利率',
                '资产负债率(%)': '资产负债率',
                '流动比率': '流动比率',
                '净资产收益率(%)': '净资产收益率(ROE)'
            }

            for target, source in mapping.items():
                s = get_series(source)
                # Special handling for percentages if needed. Abstract '毛利率' is usually 20.5 not 0.205?
                # Let's check debugging output again. We didn't print values for rates.
                # Usually akshare abstract is mixed.
                # Let's assume standard float.
                new_df[target] = s

            # Handle calculated fields for helpers
            # '主营利润比重' -> Not in abstract directly. Use 0.
            new_df['主营利润比重'] = 0.0

            # '每股收益_调整后(元)' -> Use '基本每股收益'
            new_df['每股收益_调整后(元)'] = get_series('基本每股收益')
            new_df['扣除非经常性损益后的每股收益(元)'] = get_series('基本每股收益') # Fallback

            # '股息发放率(%)' -> Not in abstract.
            new_df['股息发放率(%)'] = 0.0

            # Use the helpers (they expect a DataFrame where iloc[0] is latest)
            # new_df index is dates (newest first), so iloc[0] is latest.

            # Important: _extract_revenue expects YOY growth.
            # If '营业总收入增长率' is e.g. 0.15 (15%) or 15?
            # We might need to adjust.

            return {
                "revenue": self._extract_revenue(new_df),
                "profit": self._extract_profit(new_df),
                "cashflow": self._extract_cashflow(new_df),
                "debt": self._extract_debt(new_df),
                "shareholder_return": self._extract_shareholder_return(new_df),
                "history": self._extract_financial_history(new_df)
            }

        except Exception as e:
            logger.error(f"AkShare abstract fallback failed: {e}")
            return self._empty_indicators()

    # ========================== Sector Data ==========================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_sector_fund_flow_rank(self) -> List[Dict[str, Any]]:
        """
        [Deprecated] Get sector fund flow ranking (hot/cold sectors).
        Please use get_board_info() instead.
        """
        try:
            # 东方财富-行业资金流
            df = ak.stock_fund_flow_industry(symbol="即时")
            if df.empty: return []

            # Columns usually: 序号, 行业, 行业指数, 行业-涨跌幅, 流入资金, 流出资金, 净额, 公司家数, 领涨股, 领涨股-涨跌幅, 当前价
            rankings = []
            for _, row in df.iterrows():
                rankings.append({
                    "rank": int(row.get('序号', 0)),
                    "name": str(row.get('行业', '')),
                    "change_percent": self._safe_get(row, '行业-涨跌幅'),
                    "flow_in": self._safe_get(row, '流入资金'),
                    "flow_out": self._safe_get(row, '流出资金'),
                    "net_flow": self._safe_get(row, '净额'),
                    "company_count": int(row.get('公司家数', 0)),
                    "leading_stock": str(row.get('领涨股', '')),
                    "leading_stock_change": self._safe_get(row, '领涨股-涨跌幅')
                })
            return rankings
        except Exception as e:
            logger.error(f"AkShare get_sector_fund_flow_rank failed: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_sector_components(self, sector_name: str) -> List[Dict[str, Any]]:
        """
        [Deprecated] Get components stocks of a sector.
        Please use get_board_info() instead.
        """
        try:
            mapped_name = self._sector_mapping.get(sector_name, sector_name)
            # 东方财富-行业板块-成份股
            df = ak.stock_board_industry_cons_em(symbol=mapped_name)
            if df.empty: return []

            # Columns usually: 序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收, 换手率, 市盈率-动态, 市净率
            components = []
            for _, row in df.iterrows():
                components.append({
                    "symbol": str(row.get('代码', '')),
                    "name": str(row.get('名称', '')),
                    "price": self._safe_get(row, '最新价'),
                    "change_percent": self._safe_get(row, '涨跌幅'),
                    "volume": self._safe_get(row, '成交量'),
                    "amount": self._safe_get(row, '成交额'),
                    "turnover_rate": self._safe_get(row, '换手率'),
                    "pe": self._safe_get(row, '市盈率-动态'),
                    "pb": self._safe_get(row, '市净率')
                })
            return components
        except Exception as e:
            logger.error(f"AkShare get_sector_components failed for {sector_name}: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_concept_fund_flow_rank(self) -> List[Dict[str, Any]]:
        """
        [Deprecated] Get concept board fund flow ranking.
        Please use get_board_info() instead.
        """
        try:
            # 东方财富-概念资金流
            df = ak.stock_fund_flow_concept(symbol="即时")
            if df.empty: return []

            # Columns usually: 序号, 行业, 行业指数, 行业-涨跌幅, 流入资金, 流出资金, 净额, 公司家数, 领涨股, 领涨股-涨跌幅, 当前价
            # Note: For concept fund flow, column '行业' actually means '概念名称'
            rankings = []
            for _, row in df.iterrows():
                rankings.append({
                    "rank": int(row.get('序号', 0)),
                    "name": str(row.get('行业', '')),
                    "change_percent": self._safe_get(row, '行业-涨跌幅'),
                    "flow_in": self._safe_get(row, '流入资金'),
                    "flow_out": self._safe_get(row, '流出资金'),
                    "net_flow": self._safe_get(row, '净额'),
                    "company_count": int(row.get('公司家数', 0)),
                    "leading_stock": str(row.get('领涨股', '')),
                    "leading_stock_change": self._safe_get(row, '领涨股-涨跌幅')
                })
            return rankings
        except Exception as e:
            logger.error(f"AkShare get_concept_fund_flow_rank failed: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_concept_components(self, sector_name: str) -> List[Dict[str, Any]]:
        """
        [Deprecated] Get components stocks of a concept board.
        Please use get_board_info() instead.
        """
        try:
            mapped_name = self._concept_mapping.get(sector_name, sector_name)
            # 东方财富-概念板块-成份股
            df = ak.stock_board_concept_cons_em(symbol=mapped_name)
            if df.empty: return []

            # Columns usually: 序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收, 换手率, 市盈率-动态, 市净率
            components = []
            for _, row in df.iterrows():
                components.append({
                    "symbol": str(row.get('代码', '')),
                    "name": str(row.get('名称', '')),
                    "price": self._safe_get(row, '最新价'),
                    "change_percent": self._safe_get(row, '涨跌幅'),
                    "volume": self._safe_get(row, '成交量'),
                    "amount": self._safe_get(row, '成交额'),
                    "turnover_rate": self._safe_get(row, '换手率'),
                    "pe": self._safe_get(row, '市盈率-动态'),
                    "pb": self._safe_get(row, '市净率')
                })
            return components
        except Exception as e:
            logger.error(f"AkShare get_concept_components failed for {sector_name}: {e}")
            return []

    def get_stock_fund_flow(self, symbol: str) -> List[Dict[str, Any]]:
        """
        [Deprecated] Get individual stock fund flow history.
        Please use get_fund_flow() instead.
        """
        try:
            # 1. Infer market
            market = ""
            if len(symbol) == 6:
                if symbol.startswith("6"):
                    market = "sh"
                elif symbol.startswith("0") or symbol.startswith("3"):
                    market = "sz"
                elif symbol.startswith("4") or symbol.startswith("8"):
                    market = "bj"
                elif symbol.startswith("5"):
                    market = "sh" # ETF
                elif symbol.startswith("1"):
                    market = "sz" # ETF

            if not market:
                # Non-A-share or unsupported format
                return []

            # 2. Call AkShare
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)

            if df is None or df.empty: return []

            # 3. Format
            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": str(row['日期']),
                    "close": float(row['收盘价']),
                    "change_pct": float(row['涨跌幅']),
                    "main_net_inflow": float(row['主力净流入-净额']),
                    "main_net_ratio": float(row['主力净流入-净占比']),
                    "super_net_inflow": float(row['超大单净流入-净额']),
                    "large_net_inflow": float(row['大单净流入-净额']),
                    "medium_net_inflow": float(row['中单净流入-净额']),
                    "small_net_inflow": float(row['小单净流入-净额'])
                })

            # Sort desc by date
            result.sort(key=lambda x: x['date'], reverse=True)
            return result

        except Exception as e:
            logger.error(f"AkShare get_stock_fund_flow failed for {symbol}: {e}")
            return []

    # ========================== Macro Data ==========================

    @retry(stop=stop_after_attempt(3))
    def get_macro_data(self, indicator: str) -> Dict[str, Any]:
        """
        [Deprecated] Get latest China macro data (GDP, CPI, PMI).
        Please use get_macro() instead.
        """
        try:
            indicator_upper = indicator.upper()
            if indicator_upper == 'GDP':
                df = ak.macro_china_gdp()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China GDP",
                    "value": float(latest['国内生产总值-绝对值']),
                    "growth_rate": float(latest['国内生产总值-同比增长']),
                    "period": latest['季度'],
                    "unit": "100 Million CNY"
                }
            elif indicator_upper == 'CPI':
                df = ak.macro_china_cpi()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China CPI",
                    "value": float(latest['全国-当月']),
                    "yoy": float(latest['全国-同比增长']),
                    "date": latest['月份'],
                    "unit": "Index"
                }
            elif indicator_upper == 'PMI':
                df = ak.macro_china_pmi()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China PMI",
                    "manufacturing": float(latest['制造业-指数']),
                    "non_manufacturing": float(latest['非制造业-指数']),
                    "date": latest['月份']
                }
            elif indicator_upper == 'PPI':
                df = ak.macro_china_ppi_yearly()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China PPI",
                    "value": float(latest['今值']),
                    "date": str(latest['日期'])
                }
            elif indicator_upper == 'M2':
                df = ak.macro_china_money_supply()
                if df.empty: return {"error": "No data"}
                latest = df.iloc[0]
                return {
                    "indicator": "China M2",
                    "value": float(latest['货币和准货币(M2)-数量(亿元)']),
                    "yoy": float(latest['货币和准货币(M2)-同比增长']),
                    "date": latest['月份']
                }
            elif indicator_upper == 'LPR':
                df = ak.macro_china_lpr()
                if df.empty: return {"error": "No data"}
                # Sort by date desc to get latest
                df = df.sort_values('TRADE_DATE', ascending=False)
                latest = df.iloc[0]
                return {
                    "indicator": "China LPR",
                    "1y": float(latest['LPR1Y']),
                    "5y": float(latest['LPR5Y']),
                    "date": str(latest['TRADE_DATE'])
                }
            # elif indicator_upper == 'SOCIAL_FINANCING':
            #     # SSL Error on source
            #     pass
            return {"error": f"Unsupported indicator: {indicator}"}
        except Exception as e:
            logger.error(f"AkShare get_macro_data failed: {e}")
            return {"error": str(e)}

    @retry(stop=stop_after_attempt(3))
    def get_macro_history(self, indicator: str) -> Dict[str, Any]:
        """
        [Deprecated] Get historical China macro data.
        Please use get_macro(history=True) instead.
        """
        try:
            data = []
            indicator_upper = indicator.upper()
            if indicator_upper == 'GDP':
                df = ak.macro_china_gdp()
                for _, row in df.iterrows():
                    data.append({
                        "date": row['季度'],
                        "value": float(row['国内生产总值-绝对值']),
                        "growth": float(row['国内生产总值-同比增长'])
                    })
            elif indicator_upper == 'CPI':
                df = ak.macro_china_cpi()
                for _, row in df.iterrows():
                    data.append({
                        "date": row['月份'],
                        "value": float(row['全国-当月']),
                        "yoy": float(row['全国-同比增长'])
                    })
            elif indicator_upper == 'PMI':
                df = ak.macro_china_pmi()
                for _, row in df.iterrows():
                    data.append({
                        "date": row['月份'],
                        "value": float(row['制造业-指数']),
                        "non_manufacturing": float(row['非制造业-指数'])
                    })
            elif indicator_upper == 'PPI':
                df = ak.macro_china_ppi_yearly()
                for _, row in df.iterrows():
                    data.append({
                        "date": str(row['日期']),
                        "value": float(row['今值']),
                        "ppi": float(row['今值'])
                    })
            elif indicator_upper == 'M2':
                df = ak.macro_china_money_supply()
                for _, row in df.iterrows():
                    data.append({
                        "date": row['月份'],
                        "value": float(row['货币和准货币(M2)-数量(亿元)']),
                        "yoy": float(row['货币和准货币(M2)-同比增长'])
                    })
            elif indicator_upper == 'LPR':
                df = ak.macro_china_lpr()
                df = df.sort_values('TRADE_DATE', ascending=False)
                for _, row in df.iterrows():
                    data.append({
                        "date": str(row['TRADE_DATE']),
                        "value": float(row['LPR1Y']), # Map 1Y to value for frontend
                        "1y": float(row['LPR1Y']),
                        "5y": float(row['LPR5Y'])
                    })
            # elif indicator_upper == 'SOCIAL_FINANCING':
            # pass
            else:
                return {"error": f"Unsupported indicator: {indicator}"}

            return {"indicator": indicator, "data": data}
        except Exception as e:
            logger.error(f"AkShare get_macro_history failed: {e}")
            return {"error": str(e)}

    # ========================== Calendar / Events ==========================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_economic_calendar(self, date_str: str = None) -> List[Dict[str, Any]]:
        """
        Get economic calendar events.
        :param date_str: YYYYMMDD string. If None, use today.
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y%m%d")

            df = ak.news_economic_baidu(date=date_str)
            if df.empty:
                return []

            # Filter for key regions/events (optional, but raw data is safer for upstream filtering)
            # Columns: ['日期', '时间', '地区', '事件', '公布', '预期', '前值', '重要性']
            events = []
            for _, row in df.iterrows():
                # Filter logic can be here or in caller. Let's keep it broad but prioritize CN/US
                region = str(row['地区'])
                if region not in ["中国", "美国", "欧元区"]:
                    continue

                events.append({
                    "date": str(row['日期']),
                    "time": str(row['时间']),
                    "region": region,
                    "event": str(row['事件']),
                    "previous": row['前值'],
                    "consensus": row['预期'],
                    "actual": row['公布'],
                    "importance": row['重要性']
                })
            return events
        except Exception as e:
            logger.error(f"AkShare get_economic_calendar failed: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_headline_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get headline financial news.
        Uses TongHuaShun (stock_info_global_ths) as source.
        """
        try:
            # Columns: 标题, 内容, 发布时间, 链接
            df = ak.stock_info_global_ths()
            if df.empty:
                return []

            news = []
            for _, row in df.head(limit).iterrows():
                news.append({
                    "title": str(row['标题']),
                    "publish_time": str(row['发布时间']),
                    "link": str(row['链接']),
                    "content": str(row['内容']) if row.get('内容') else str(row['标题']) # Content might be short
                })
            return news
        except Exception as e:
            logger.error(f"AkShare get_headline_news (THS) failed: {e}")
            return []

    # ========================== Helpers ==========================

    def _validate_symbol(self, symbol: str) -> bool:
        return len(symbol) == 6 and symbol.isdigit()

    def _safe_get(self, row, key, default=0.0):
        val = row.get(key, default)
        if pd.isna(val): return default
        try: return float(val)
        except: return default

    def _empty_indicators(self):
        return {k: {} for k in ["revenue", "profit", "cashflow", "debt", "shareholder_return"]} | {"history": []}

    # Extraction helpers (simplified)
    def _extract_revenue(self, df):
        latest = df.iloc[0]
        return {
            "revenue_yoy": round(self._safe_get(latest, '主营业务收入增长率(%)'), 2),
            "core_revenue_ratio": round(self._safe_get(latest, '主营利润比重'), 2),
            "cash_to_revenue": 1.0 if self._safe_get(latest, '每股经营性现金流(元)') > 0 else 0.0
        }

    def _extract_profit(self, df):
        latest = df.iloc[0]
        return {
            "non_recurring_eps": round(self._safe_get(latest, '扣除非经常性损益后的每股收益(元)'), 4),
            "gross_margin": round(self._safe_get(latest, '销售毛利率(%)'), 2),
            "net_margin": round(self._safe_get(latest, '销售净利率(%)'), 2)
        }

    def _extract_cashflow(self, df):
        latest = df.iloc[0]
        ocf = self._safe_get(latest, '每股经营性现金流(元)')
        eps = self._safe_get(latest, '每股收益_调整后(元)', 1.0)
        return {
            "ocf_to_net_profit": round(ocf / eps if eps != 0 else 0.0, 2),
            "free_cash_flow": None
        }

    def _extract_debt(self, df):
        latest = df.iloc[0]
        return {
            "asset_liability_ratio": round(self._safe_get(latest, '资产负债率(%)'), 2),
            "current_ratio": round(self._safe_get(latest, '流动比率'), 2)
        }

    def _extract_shareholder_return(self, df):
        latest = df.iloc[0]
        return {
            "dividend_yield": round(self._safe_get(latest, '股息发放率(%)'), 2),
            "roe": round(self._safe_get(latest, '净资产收益率(%)'), 2)
        }

    def _extract_financial_history(self, df):
        history = []
        for _, row in df.iterrows():
            history.append({
                "date": str(row.get('日期', '')),
                "roe": round(self._safe_get(row, '净资产收益率(%)'), 2),
                "gross_margin": round(self._safe_get(row, '销售毛利率(%)'), 2),
                "net_margin": round(self._safe_get(row, '销售净利率(%)'), 2),
                "asset_liability_ratio": round(self._safe_get(row, '资产负债率(%)'), 2)
            })
        return history

if __name__ == "__main__":
    # export PYTHONPATH=$PYTHONPATH:. && python3 backend/infrastructure/market/akshare_tool.py
    tool = AkShareTool()

    print("\n=== Test get_quote ===")
    print("A-Share (600036):", tool.get_quote("600036"))
    print("ETF (510300):", tool.get_quote("510300"))
    # print("HK (00700):", tool.get_quote("00700", market="HK"))
    # print("US (AAPL):", tool.get_quote("AAPL", market="US"))

    print("\n=== Test get_indices_quote ===")
    print("CN Indices:", tool.get_indices_quote("CN")[:2])
    print("HK Indices:", tool.get_indices_quote("HK"))
    print("US Indices:", tool.get_indices_quote("US"))

    print("\n=== Test get_index_history ===")
    print("CN Index Hist (上证):", len(tool.get_index_history("上证指数")))
    print("HK Index Hist (HSI):", len(tool.get_index_history("HSI")))
    print("US Index Hist (.DJI):", len(tool.get_index_history(".DJI")))

    print("\n=== Test get_history ===")
    hist = tool.get_history("600036", period="daily")
    print(f"A History len: {len(hist)}")
    if hist: print("Sample A:", hist[0])

    hist = tool.get_history("00700", period="daily")
    print(f"HK History len: {len(hist)}")
    if hist: print("Sample HK:", hist[0])

    hist = tool.get_history("AAPL", period="daily")
    print(f"US History len: {len(hist)}")
    if hist: print("Sample US:", hist[0])

    print("\n=== Test get_fund_flow ===")
    flow = tool.get_fund_flow("600036")
    print(f"Flow len: {len(flow)}")
    if flow: print("Latest A Flow:", flow[0])

    flow = tool.get_fund_flow("00700")
    print(f"HK Flow len: {len(flow)}")
    if flow: print("Latest HK Flow:", flow[0])

    flow = tool.get_fund_flow("AAPL")
    print(f"US Flow len: {len(flow)}")
    if flow: print("Latest US Flow:", flow[0])

    print("\n=== Test get_board_info ===")
    ranks = tool.get_board_info(info_type="rank")
    print(f"Sector Ranks len: {len(ranks)}")
    if ranks: print("Top 1 Sector:", ranks[0])

    print("\n=== Test get_financials ===")
    fin = tool.get_financials("600036")
    print("Financials Keys:", fin.keys())

    print("\n=== Test get_macro ===")
    gdp = tool.get_macro("GDP")
    print("GDP:", gdp)
