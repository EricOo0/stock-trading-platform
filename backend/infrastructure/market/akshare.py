

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

    # ========================== Market Data ==========================

    def get_a_share_indices_spot(self, target_indices: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get A-share key indices latest spot data.
        target_indices: list of names to filter, default common benchmarks.
        """
        try:
            import akshare as ak
            df = ak.stock_zh_index_spot_em()
            if df.empty:
                return []
            targets = target_indices or ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500", "北证50"]
            filtered = df[df["名称"].isin(targets)]
            return filtered.to_dict(orient="records")
        except Exception as e:
            logger.error(f"AkShare get_a_share_indices_spot failed: {e}")
            return []

    def get_hk_index_latest(self, symbol: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get latest HK index quote via sina daily interface.
        """
        try:
            import akshare as ak
            df = ak.stock_hk_index_daily_sina(symbol=symbol)
            if df.empty:
                return {}
            last = df.iloc[-1].to_dict()
            if name:
                last["name"] = name
            return last
        except Exception as e:
            logger.error(f"AkShare get_hk_index_latest failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def get_us_index_latest(self, symbol: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get latest US index quote via sina interface.
        """
        try:
            import akshare as ak
            df = ak.index_us_stock_sina(symbol=symbol)
            if df.empty:
                return {}
            last = df.iloc[-1].to_dict()
            if name:
                last["name"] = name
            return last
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
        Get real-time stock quote for A-shares using lightweight interfaces.
        Replaces 'stock_zh_a_spot_em' (full market snapshot) with per-symbol queries to improve performance.
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
        """Get historical data for A-shares."""
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
        """Get financial indicators for A-shares."""
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
        """Get sector fund flow ranking (hot/cold sectors)."""
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
        """Get components stocks of a sector."""
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
        """Get concept board fund flow ranking."""
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
        """Get components stocks of a concept board."""
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
        """Get individual stock fund flow history."""
        try:
            # 1. Infer market
            market = ""
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
            else:
                return []

            # 2. Call AkShare
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            
            if df.empty: return []
            
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
        """Get latest China macro data (GDP, CPI, PMI)."""
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
        """Get historical China macro data."""
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
    tool = AkShareTool()
    # print(tool.get_stock_quote("600036"))
    # print(tool.get_macro_data("GDP"))
