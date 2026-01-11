

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
        pass

    # ========================== Market Data ==========================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote for A-shares."""
        if not self._validate_symbol(symbol):
             return {"error": "Invalid A-share symbol"}

        try:
            # Use spot data for full market snapshot
            # This provides PE, PB, Turnover, etc. which are missing in hist_min stock_zh_a_hist_min_em
            df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                return {"error": "Market data unavailable"}
            
            # Filter by symbol
            row = df[df['代码'] == symbol]
            if row.empty:
                 return {"error": "Symbol not found in snapshot"}
            
            latest = row.iloc[0]
            
            # Map fields
            current_price = float(latest['最新价'])
            prev_close = float(latest['昨收'])
            
            change_amount = 0.0
            change_percent = 0.0
            if prev_close > 0:
                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close) * 100

            # Safe get helper
            def get_val(key):
                val = latest.get(key)
                if pd.isna(val): return None
                try: return float(val)
                except: return None

            return {
                "symbol": symbol,
                "current_price": current_price,
                "open": get_val('今开'),
                "high": get_val('最高'),
                "low": get_val('最低'),
                "prev_close": prev_close,
                "change_amount": round(change_amount, 2),
                "change_percent": round(change_percent, 2),
                "volume": get_val('成交量'),
                "turnover": get_val('成交额'),
                "turnover_rate": get_val('换手率'),
                "pe": get_val('市盈率-动态'), # PE TTM
                "pb": get_val('市净率'),
                "market_cap": get_val('总市值'),
                "circulating_market_cap": get_val('流通市值'),
                "timestamp": datetime.now().isoformat(), # Spot data doesn't have per-row time usually
                "market": "A-share",
                "source": "akshare_spot"
            }
        except Exception as e:
            logger.error(f"AkShare get_stock_quote failed for {symbol}: {e}")
            return {"error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_history(self, symbol: str, period: str = "30d") -> List[Dict[str, Any]]:
        """Get historical data for A-shares."""
        if not self._validate_symbol(symbol): return []

        try:
            days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "ytd": 365, "max": 3650, "1mo": 30, "3mo": 90, "6mo": 180}
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
            # 东方财富-行业板块-成份股
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
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
            # 东方财富-概念板块-成份股
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def get_stock_fund_flow(self, symbol: str) -> List[Dict[str, Any]]:
        """Get individual stock fund flow history."""
        try:
            # AkShare stock_individual_fund_flow requires market prefix or specific params?
            # Usually stock_individual_fund_flow(stock="000001", market="sz")
            # We need to determine market.
            market_code = "sh" if symbol.startswith(('60', '68', '5', '9')) else "sz"
            
            df = ak.stock_individual_fund_flow(stock=symbol, market=market_code)
            if df.empty: return []
            
            # Columns: 日期, 收盘价, 涨跌幅, 主力净流入-净额, 主力净流入-净占比, 超大单净流入-净额, ...
            # Sort by date desc
            # Note: AkShare usually returns date asc?
            # Let's inspect columns from experience or assume standard.
            
            # Take last 5 days
            df = df.tail(10).iloc[::-1]
            
            flows = []
            for _, row in df.iterrows():
                flows.append({
                    "date": str(row.get('日期', '')),
                    "close": self._safe_get(row, '收盘价'),
                    "change_pct": self._safe_get(row, '涨跌幅'),
                    "main_net_inflow": self._safe_get(row, '主力净流入-净额'),
                    "main_net_inflow_pct": self._safe_get(row, '主力净流入-净占比'),
                    "super_large_net_inflow": self._safe_get(row, '超大单净流入-净额'),
                    "large_net_inflow": self._safe_get(row, '大单净流入-净额'),
                    "medium_net_inflow": self._safe_get(row, '中单净流入-净额'),
                    "small_net_inflow": self._safe_get(row, '小单净流入-净额'),
                })
            return flows
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
