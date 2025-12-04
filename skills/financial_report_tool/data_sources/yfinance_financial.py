"""
yfinance财务数据源
专注于美股和港股市场的财务指标获取
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any
from loguru import logger
from .base_financial import BaseFinancialSource

class YFinanceFinancialSource(BaseFinancialSource):
    """yfinance财务数据源 - 美股/港股"""
    
    def get_raw_data(self, symbol: str, years: int) -> Dict[str, Any]:
        """
        获取yfinance三大财务报表
        
        Args:
            symbol: 股票代码 (yfinance格式, 如 AAPL, 0700.HK)
            years: 获取年数
            
        Returns:
            包含三大报表和info的字典
        """
        try:
            logger.info(f"Fetching yfinance financial data for {symbol}")
            ticker = yf.Ticker(symbol)
            
            return {
                "financials": ticker.financials,
                "balance_sheet": ticker.balance_sheet,
                "cashflow": ticker.cashflow,
                "info": ticker.info
            }
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return {
                "financials": pd.DataFrame(),
                "balance_sheet": pd.DataFrame(),
                "cashflow": pd.DataFrame(),
                "info": {}
            }
    
    def extract_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从yfinance三表中提取5大类财务指标
        
        Args:
            data: 包含三大报表的字典
            
        Returns:
            5大类指标字典
        """
        financials = data.get("financials", pd.DataFrame())
        balance_sheet = data.get("balance_sheet", pd.DataFrame())
        cashflow = data.get("cashflow", pd.DataFrame())
        info = data.get("info", {})
        
        if financials.empty and balance_sheet.empty and cashflow.empty:
            return self._empty_indicators()
        
        try:
            return {
                "revenue": self._extract_revenue(financials, cashflow),
                "profit": self._extract_profit(financials),
                "cashflow": self._extract_cashflow(cashflow, financials),
                "debt": self._extract_debt(balance_sheet),
                "shareholder_return": self._extract_shareholder_return(info, financials, balance_sheet),
                "history": self._extract_history(financials, balance_sheet)
            }
        except Exception as e:
            logger.error(f"Error extracting yfinance indicators: {e}")
            return self._empty_indicators()
    
    def _extract_revenue(self, financials: pd.DataFrame, cashflow: pd.DataFrame) -> Dict[str, float]:
        """收入端指标"""
        if financials.empty:
            return {}
        
        try:
            # 营业收入YoY
            revenue_yoy = 0.0
            if 'Total Revenue' in financials.index and len(financials.columns) >= 2:
                latest_revenue = self._safe_get_value(financials, 'Total Revenue', 0)
                prev_revenue = self._safe_get_value(financials, 'Total Revenue', 1)
                if prev_revenue != 0:
                    revenue_yoy = ((latest_revenue - prev_revenue) / prev_revenue) * 100
            
            # 核心营收占比 (yfinance不提供,设为None)
            core_revenue_ratio = None
            
            # 现金收入比
            cash_to_revenue = 0.0
            if not cashflow.empty and 'Operating Cash Flow' in cashflow.index:
                ocf = self._safe_get_value(cashflow, 'Operating Cash Flow', 0)
                latest_revenue = self._safe_get_value(financials, 'Total Revenue', 0)
                if latest_revenue != 0:
                    cash_to_revenue = ocf / latest_revenue
            
            return {
                "revenue_yoy": round(revenue_yoy, 2),
                "core_revenue_ratio": core_revenue_ratio,
                "cash_to_revenue": round(cash_to_revenue, 2)
            }
        except Exception as e:
            logger.error(f"Error extracting revenue: {e}")
            return {}
    
    def _extract_profit(self, financials: pd.DataFrame) -> Dict[str, float]:
        """利润端指标"""
        if financials.empty:
            return {}
        
        try:
            net_income = self._safe_get_value(financials, 'Net Income', 0)
            revenue = self._safe_get_value(financials, 'Total Revenue', 0)
            gross_profit = self._safe_get_value(financials, 'Gross Profit', 0)
            
            # 扣非归母净利 (yfinance用Net Income近似)
            non_recurring_net_profit = net_income
            
            # 经营毛利率
            gross_margin = (gross_profit / revenue * 100) if revenue != 0 else 0.0
            
            # 核心净利率
            net_margin = (net_income / revenue * 100) if revenue != 0 else 0.0
            
            return {
                "non_recurring_net_profit": round(non_recurring_net_profit, 2),
                "gross_margin": round(gross_margin, 2),
                "net_margin": round(net_margin, 2)
            }
        except Exception as e:
            logger.error(f"Error extracting profit: {e}")
            return {}
    
    def _extract_cashflow(self, cashflow: pd.DataFrame, financials: pd.DataFrame) -> Dict[str, float]:
        """现金流指标"""
        if cashflow.empty:
            return {}
        
        try:
            # 经营现金流/归母净利
            ocf = self._safe_get_value(cashflow, 'Operating Cash Flow', 0)
            net_income = self._safe_get_value(financials, 'Net Income', 0) if not financials.empty else 1.0
            ocf_to_net_profit = (ocf / net_income) if net_income != 0 else 0.0
            
            # 自由现金流
            fcf = self._safe_get_value(cashflow, 'Free Cash Flow', 0)
            
            return {
                "ocf_to_net_profit": round(ocf_to_net_profit, 2),
                "free_cash_flow": round(fcf, 2) if fcf else None
            }
        except Exception as e:
            logger.error(f"Error extracting cashflow: {e}")
            return {}
    
    def _extract_debt(self, balance_sheet: pd.DataFrame) -> Dict[str, float]:
        """负债端指标"""
        if balance_sheet.empty:
            return {}
        
        try:
            total_assets = self._safe_get_value(balance_sheet, 'Total Assets', 0)
            total_liabilities = self._safe_get_value(balance_sheet, 'Total Liabilities Net Minority Interest', 0)
            
            # 资产负债率
            asset_liability_ratio = (total_liabilities / total_assets * 100) if total_assets != 0 else 0.0
            
            # 流动比率 (yfinance可能缺少Current Assets/Liabilities)
            current_ratio = None
            if 'Current Assets' in balance_sheet.index and 'Current Liabilities' in balance_sheet.index:
                current_assets = self._safe_get_value(balance_sheet, 'Current Assets', 0)
                current_liabilities = self._safe_get_value(balance_sheet, 'Current Liabilities', 0)
                if current_liabilities != 0:
                    current_ratio = current_assets / current_liabilities
            
            return {
                "asset_liability_ratio": round(asset_liability_ratio, 2),
                "current_ratio": round(current_ratio, 2) if current_ratio else None
            }
        except Exception as e:
            logger.error(f"Error extracting debt: {e}")
            return {}
    
    def _extract_shareholder_return(self, info: Dict, financials: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict[str, float]:
        """股东回报指标"""
        try:
            # 股息率
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0.0
            
            # ROE
            roe = 0.0
            if not financials.empty and not balance_sheet.empty:
                net_income = self._safe_get_value(financials, 'Net Income', 0)
                equity = self._safe_get_value(balance_sheet, 'Stockholders Equity', 0)
                if equity != 0:
                    roe = (net_income / equity) * 100
            
            return {
                "dividend_yield": round(dividend_yield, 2),
                "roe": round(roe, 2)
            }
        except Exception as e:
            logger.error(f"Error extracting shareholder return: {e}")
            return {}
    
    def _extract_history(self, financials: pd.DataFrame, balance_sheet: pd.DataFrame) -> list:
        """提取历史数据"""
        history = []
        
        try:
            if financials.empty:
                return history
            
            for i in range(min(len(financials.columns), 4)):  # 最多4年
                revenue = self._safe_get_value(financials, 'Total Revenue', i)
                net_income = self._safe_get_value(financials, 'Net Income', i)
                gross_profit = self._safe_get_value(financials, 'Gross Profit', i)
                
                gross_margin = (gross_profit / revenue * 100) if revenue != 0 else 0.0
                net_margin = (net_income / revenue * 100) if revenue != 0 else 0.0
                
                # ROE
                roe = 0.0
                if not balance_sheet.empty and i < len(balance_sheet.columns):
                    equity = self._safe_get_value(balance_sheet, 'Stockholders Equity', i)
                    if equity != 0:
                        roe = (net_income / equity) * 100
                
                date = str(financials.columns[i].date()) if i < len(financials.columns) else ""
                
                history.append({
                    "date": date,
                    "roe": round(roe, 2),
                    "gross_margin": round(gross_margin, 2),
                    "net_margin": round(net_margin, 2)
                })
        except Exception as e:
            logger.error(f"Error extracting history: {e}")
        
        return history
    
    @staticmethod
    def _safe_get_value(df: pd.DataFrame, index_name: str, col_index: int) -> float:
        """安全获取DataFrame值"""
        try:
            if index_name not in df.index:
                return 0.0
            if col_index >= len(df.columns):
                return 0.0
            value = df.loc[index_name].iloc[col_index]
            if pd.isna(value):
                return 0.0
            return float(value)
        except (KeyError, IndexError, ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def _empty_indicators() -> Dict[str, Any]:
        """返回空指标结构"""
        return {
            "revenue": {},
            "profit": {},
            "cashflow": {},
            "debt": {},
            "shareholder_return": {},
            "history": []
        }
